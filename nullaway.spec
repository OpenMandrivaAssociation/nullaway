Name:		nullaway
Version:	0.14.4
Release:	1
Summary:	Error Prone checker for nullness
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/uber/NullAway
# Tag v0.14.4 with the Gradle wrapper jar removed.
Source0:	nullaway-%{version}.tar.gz
# Tag v0.13.7 with the Gradle wrapper jar removed.
Source1:	nullaway-0.13.7.tar.gz

%{!?dataflow_jar:%global dataflow_jar %{_javadir}/dataflow-nullaway.jar}
%{!?dataflow_old_jar:%global dataflow_old_jar %{_javadir}/dataflow-nullaway-4.0.0.jar}
%{!?plume_jar:%global plume_jar %{_javadir}/plume-util.jar}
%{!?plume_old_jar:%global plume_old_jar %{_javadir}/plume-util-1.8.1.jar}
%{!?reflection_jar:%global reflection_jar %{_javadir}/reflection-util.jar}
%{!?hashmap_jar:%global hashmap_jar %{_javadir}/hashmap-util.jar}

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(com.google.errorprone:error_prone_check_api) = 2.50.0
BuildRequires:	mvn(com.google.errorprone:error_prone_annotation) = 2.50.0
BuildRequires:	mvn(com.google.errorprone:error_prone_annotations) = 2.52.0
BuildRequires:	mvn(org.checkerframework:dataflow-nullaway) = 4.4.0
BuildRequires:	mvn(org.checkerframework:dataflow-nullaway) = 4.0.0
BuildRequires:	mvn(com.google.guava:guava) = 33.6.0-jre
BuildRequires:	mvn(org.jspecify:jspecify) = 1.0.0
BuildRequires:	mvn(org.jetbrains:annotations) = 26.1.0
BuildRequires:	mvn(javax.inject:javax.inject) = 1.0.5
BuildRequires:	mvn(com.google.code.findbugs:jsr305) = 3.0.2
BuildRequires:	mvn(com.google.auto.service:auto-service-annotations) = 1.1.1
BuildRequires:	mvn(org.plumelib:plume-util) = 2.0.0
BuildRequires:	mvn(org.plumelib:plume-util) = 1.8.1
BuildRequires:	mvn(org.plumelib:reflection-util) = 2.0.0
BuildRequires:	mvn(org.plumelib:hashmap-util) = 2.0.0
BuildRequires:	mvn(org.checkerframework:checker-qual) = 4.4.0
Requires:	mvn(com.uber.nullaway:nullaway-annotations) = %{version}
Requires:	mvn(com.uber.nullaway:nullaway-annotations) = 0.13.7
Requires:	mvn(com.google.errorprone:error_prone_check_api) = 2.50.0
Requires:	mvn(com.google.errorprone:error_prone_annotation) = 2.50.0
Requires:	mvn(com.google.errorprone:error_prone_annotations) = 2.52.0
Requires:	mvn(org.checkerframework:dataflow-nullaway) = 4.4.0
Requires:	mvn(org.checkerframework:dataflow-nullaway) = 4.0.0
Requires:	mvn(com.google.guava:guava) = 33.6.0-jre
Requires:	mvn(org.jspecify:jspecify) = 1.0.0
Requires:	mvn(org.jetbrains:annotations) = 26.1.0
Requires:	mvn(javax.inject:javax.inject) = 1.0.5
Requires:	mvn(com.google.code.findbugs:jsr305) = 3.0.2
Requires:	mvn(org.plumelib:plume-util) = 2.0.0
Requires:	mvn(org.plumelib:plume-util) = 1.8.1
Requires:	mvn(org.plumelib:reflection-util) = 2.0.0
Requires:	mvn(org.plumelib:hashmap-util) = 2.0.0
Requires:	mvn(org.checkerframework:checker-qual) = 4.4.0

%description
NullAway %{version} is the current Error Prone nullness checker. The
checker and its annotation jar are compiled with javac. Dataflow comes
from dataflow-nullaway 4.4.0, whose packages are
org.checkerframework.nullaway.dataflow and javacutil. Upstream declares
dataflow-nullaway 4.3.1; 4.4.0 is the current Checker Framework release
and this checker compiles against it. The 0.13.7 jars stay as side jars
so Gradle 9.9.1's request for that version still resolves. AutoService
is not run. The 0.14.4 service file lists NullAway,
RequireExplicitNullMarking, and JSpecifyUnrecognizedAnnotationLocation.

%prep
%autosetup -N -n NullAway-%{version}
tar -C %{_builddir} -xzf %{SOURCE1}
for dir in "%{_builddir}/NullAway-%{version}" "%{_builddir}/NullAway-0.13.7"; do
	find "$dir" -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > "$dir/binaries.list"
	find "$dir" -type d -name '*.jar' -print >> "$dir/binaries.list"
	if [ -s "$dir/binaries.list" ]; then
		cat "$dir/binaries.list"
		exit 1
	fi
done

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
compile_tree() {
	root=$1
	ann_expect=$2
	na_expect=$3
	extra=$4
	cp_rest=$5
	ver=$6
	svc_expect=$7
	cd "$root"
	mkdir -p classes/annotations classes/nullaway
	find annotations/src/main/java -name '*.java' > annotations.list
	test "$(wc -l < annotations.list)" -eq "$ann_expect"
	javac --release 11 -encoding UTF-8 -Xlint:-options,-removal -proc:none \
		-d classes/annotations @annotations.list
	javap -v -classpath classes/annotations com.uber.nullaway.annotations.Initializer | grep -F -q 'major version: 55'
	jar cf nullaway-annotations.jar -C classes/annotations .
	jar i nullaway-annotations.jar
	find nullaway/src/main/java -name '*.java' > nullaway.list
	if [ -n "$extra" ]; then
		printf '%%s\n' "$extra" >> nullaway.list
	fi
	test "$(wc -l < nullaway.list)" -eq "$na_expect"
	: > javac.args
	echo -encoding >> javac.args
	echo UTF-8 >> javac.args
	echo -Xlint:-options,-removal,-processing,-this-escape >> javac.args
	echo -proc:none >> javac.args
	echo -cp >> javac.args
	echo "nullaway-annotations.jar:${cp_rest}" >> javac.args
	for p in api file code comp main model parser processing tree util; do
		echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> javac.args
	done
	echo "--add-exports=jdk.compiler/com.sun.source.tree=ALL-UNNAMED" >> javac.args
	echo -d >> javac.args
	echo classes/nullaway >> javac.args
	cat nullaway.list >> javac.args
	javac @javac.args
	mkdir -p classes/nullaway/META-INF/services
	cat "$svc_expect" > classes/nullaway/META-INF/services/com.google.errorprone.bugpatterns.BugChecker
	jar cf nullaway.jar -C classes/nullaway .
	jar i nullaway.jar
	javap -v -classpath nullaway.jar com.uber.nullaway.NullAway | grep -F -q 'major version: 71'
	jar tf nullaway.jar | grep -F -q 'META-INF/services/com.google.errorprone.bugpatterns.BugChecker'
	desc=$(jar --describe-module --file nullaway.jar)
	if printf '%%s\n' "$desc" | grep -F -q 'Unable'; then
		printf '%%s\n' "$desc"
		exit 1
	fi
	if jar tf nullaway.jar | grep -E '\.(java|jar|so|node|wasm)$'; then
		exit 1
	fi
}
write_pom() {
	file=$1
	artifact=$2
	ver=$3
	deps=$4
	cat > "$file" << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.uber.nullaway</groupId>
  <artifactId>$artifact</artifactId>
  <version>$ver</version>
  <name>$artifact</name>
  <description>NullAway $artifact $ver.</description>
  <url>https://github.com/uber/NullAway</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
      <distribution>repo</distribution>
    </license>
  </licenses>
$deps
</project>
END
}
req_dep() {
	printf '    <dependency>\n      <groupId>%%s</groupId>\n      <artifactId>%%s</artifactId>\n      <version>%%s</version>\n    </dependency>\n' "$1" "$2" "$3"
}
common="%{_javadir}/auto-service-annotations.jar:%{_javadir}/jspecify.jar:%{_javadir}/org.jetbrains.annotations.jar:%{_javadir}/atinject.jar:%{_javadir}/error_prone_annotation.jar:%{_javadir}/error_prone_check_api.jar:%{_javadir}/guava.jar:%{_javadir}/javax.annotation.jar:%{_javadir}/checker-qual.jar"
old_rest="${common}:%{dataflow_old_jar}:%{plume_old_jar}"
new_rest="${common}:%{_javadir}/error_prone_annotations.jar:%{dataflow_jar}:%{plume_jar}:%{reflection_jar}:%{hashmap_jar}:%{_javadir}/failureaccess.jar"
old_svc=/tmp/nullaway-services-0.13.7
new_svc=/tmp/nullaway-services-0.14.4
printf '%%s\n' com.uber.nullaway.NullAway com.uber.nullaway.RequireExplicitNullMarking > "$old_svc"
printf '%%s\n' com.uber.nullaway.NullAway com.uber.nullaway.RequireExplicitNullMarking com.uber.nullaway.JSpecifyUnrecognizedAnnotationLocation > "$new_svc"
compile_tree "%{_builddir}/NullAway-0.13.7" 8 113 "" "$old_rest" 0.13.7 "$old_svc"
compile_tree "%{_builddir}/NullAway-%{version}" 8 122 "%{_builddir}/NullAway-%{version}/library-model/library-model-generator/src/shared/java/com/uber/nullaway/libmodel/NestedAnnotationInfo.java" "$new_rest" 0.14.4 "$new_svc"
for root in "%{_builddir}/NullAway-0.13.7" "%{_builddir}/NullAway-%{version}"; do
	(
		cd "$root"
		jar xf nullaway.jar META-INF/services/com.google.errorprone.bugpatterns.BugChecker
	)
done
grep -F -q 'com.uber.nullaway.NullAway' %{_builddir}/NullAway-0.13.7/META-INF/services/com.google.errorprone.bugpatterns.BugChecker
if grep -F -q 'JSpecifyUnrecognizedAnnotationLocation' %{_builddir}/NullAway-0.13.7/META-INF/services/com.google.errorprone.bugpatterns.BugChecker; then
	exit 1
fi
grep -F -q 'com.uber.nullaway.JSpecifyUnrecognizedAnnotationLocation' %{_builddir}/NullAway-%{version}/META-INF/services/com.google.errorprone.bugpatterns.BugChecker
{
	printf '%%s\n' '  <dependencies>'
	req_dep com.uber.nullaway nullaway-annotations 0.13.7
	req_dep com.google.errorprone error_prone_check_api 2.50.0
	req_dep com.google.errorprone error_prone_annotation 2.50.0
	req_dep org.checkerframework dataflow-nullaway 4.0.0
	req_dep com.google.guava guava 33.6.0-jre
	req_dep org.jspecify jspecify 1.0.0
	req_dep javax.inject javax.inject 1.0.5
	req_dep com.google.code.findbugs jsr305 3.0.2
	req_dep org.plumelib plume-util 1.8.1
	req_dep org.checkerframework checker-qual 4.4.0
	printf '%%s\n' '  </dependencies>'
} > /tmp/nullaway-deps-0.13.7
{
	printf '%%s\n' '  <dependencies>'
	req_dep com.uber.nullaway nullaway-annotations 0.14.4
	req_dep com.google.errorprone error_prone_check_api 2.50.0
	req_dep com.google.errorprone error_prone_annotation 2.50.0
	req_dep com.google.errorprone error_prone_annotations 2.52.0
	req_dep org.checkerframework dataflow-nullaway 4.4.0
	req_dep com.google.guava guava 33.6.0-jre
	req_dep org.jspecify jspecify 1.0.0
	req_dep org.jetbrains annotations 26.1.0
	req_dep javax.inject javax.inject 1.0.5
	req_dep com.google.code.findbugs jsr305 3.0.2
	req_dep org.plumelib plume-util 2.0.0
	req_dep org.plumelib reflection-util 2.0.0
	req_dep org.plumelib hashmap-util 2.0.0
	req_dep org.checkerframework checker-qual 4.4.0
	printf '%%s\n' '  </dependencies>'
} > /tmp/nullaway-deps-0.14.4
write_pom %{_builddir}/NullAway-0.13.7/nullaway-annotations.pom nullaway-annotations 0.13.7 ''
write_pom %{_builddir}/NullAway-0.13.7/nullaway.pom nullaway 0.13.7 "$(cat /tmp/nullaway-deps-0.13.7)"
write_pom %{_builddir}/NullAway-%{version}/nullaway-annotations.pom nullaway-annotations 0.14.4 ''
write_pom %{_builddir}/NullAway-%{version}/nullaway.pom nullaway 0.14.4 "$(cat /tmp/nullaway-deps-0.14.4)"
grep -F -q '<version>0.14.4</version>' %{_builddir}/NullAway-%{version}/nullaway.pom
grep -F -q '<version>0.13.7</version>' %{_builddir}/NullAway-0.13.7/nullaway.pom
grep -F -q '<artifactId>dataflow-nullaway</artifactId>' %{_builddir}/NullAway-%{version}/nullaway.pom

%install
set -eo pipefail
install_side() {
	pom=$1
	jar=$2
	file_name=$3
	artifact=$4
	ver=$5
	sysjar install --buildroot %{buildroot} \
		--artifact "${pom}:${jar}" \
		--file-name "$file_name" \
		--filelist ".mfiles-${file_name}"
	index="%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${artifact}.sysjar"
	test -f "$index"
	/bin/mv "$index" "%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${artifact}-${ver}.sysjar"
	sed -i "s|/usr/share/sysjar/index/com\\.uber\\.nullaway/${artifact}\\.sysjar|/usr/share/sysjar/index/com.uber.nullaway/${artifact}-${ver}.sysjar|" ".mfiles-${file_name}"
	grep -F -q "\"version\": \"${ver}\"" "%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${artifact}-${ver}.sysjar"
}
install_winner() {
	pom=$1
	jar=$2
	file_name=$3
	ver=$4
	sysjar install --buildroot %{buildroot} \
		--artifact "${pom}:${jar}" \
		--file-name "$file_name" \
		--filelist ".mfiles-${file_name}"
	idx="%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${file_name}.sysjar"
	grep -F -q "\"version\": \"${ver}\"" "$idx"
}
old="%{_builddir}/NullAway-0.13.7"
new="%{_builddir}/NullAway-%{version}"
install_side "$old/nullaway-annotations.pom" "$old/nullaway-annotations.jar" nullaway-annotations-0.13.7 nullaway-annotations 0.13.7
install_side "$old/nullaway.pom" "$old/nullaway.jar" nullaway-0.13.7 nullaway 0.13.7
install_winner "$new/nullaway-annotations.pom" "$new/nullaway-annotations.jar" nullaway-annotations 0.14.4
install_winner "$new/nullaway.pom" "$new/nullaway.jar" nullaway 0.14.4
test -s %{buildroot}%{_javadir}/nullaway-0.13.7.jar
test -s %{buildroot}%{_javadir}/nullaway-annotations-0.13.7.jar
test -s %{buildroot}%{_javadir}/nullaway.jar
test -s %{buildroot}%{_javadir}/nullaway-annotations.jar
: > .mfiles
for list in .mfiles-nullaway-annotations-0.13.7 .mfiles-nullaway-0.13.7 .mfiles-nullaway-annotations .mfiles-nullaway
do
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
	done < "$list"
done
grep -F -q '/nullaway.jar' .mfiles
grep -F -q '/nullaway-0.13.7.jar' .mfiles
grep -F -q '/nullaway-annotations.jar' .mfiles
grep -F -q '/nullaway-annotations-0.13.7.jar' .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import com.google.errorprone.BugPattern;
import com.uber.nullaway.NullAway;
import java.util.Arrays;
import org.checkerframework.nullaway.dataflow.cfg.node.MethodInvocationNode;

public class Smoke {
	public static void main(String[] args) throws Exception {
		NullAway checker = new NullAway();
		BugPattern ann = NullAway.class.getAnnotation(BugPattern.class);
		if (ann == null || !"Nullability type error.".equals(ann.summary())) {
			throw new AssertionError(String.valueOf(ann));
		}
		if (!Arrays.asList(ann.altNames()).contains("CheckNullabilityTypes")) {
			throw new AssertionError(Arrays.toString(ann.altNames()));
		}
		String canonical = checker.canonicalName();
		if (!"NullAway".equals(canonical)) {
			throw new AssertionError(canonical);
		}
		Class<?> param = NullAway.class
			.getMethod("isMethodUnannotated", MethodInvocationNode.class)
			.getParameterTypes()[0];
		if (!"org.checkerframework.nullaway.dataflow.cfg.node.MethodInvocationNode".equals(param.getName())) {
			throw new AssertionError(param.getName());
		}
		if (checker.getConfig() == null) {
			throw new AssertionError("config");
		}
		System.out.println(args[0] + " " + canonical + " " + checker.getConfig().getClass().getSimpleName());
	}
}
EOF
run_check() {
	label=$1
	checker=$2
	annotations=$3
	flow=$4
	plume=$5
	extra=$6
	outdir=$7
	base="%{_javadir}/error_prone_check_api.jar:%{_javadir}/error_prone_annotation.jar:%{_javadir}/error_prone_annotations.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar:%{_javadir}/jspecify.jar:%{_javadir}/atinject.jar:%{_javadir}/javax.annotation.jar:%{_javadir}/checker-qual.jar:%{_javadir}/org.jetbrains.annotations.jar"
	cp="${checker}:${annotations}:${flow}:${plume}:${extra}:${base}"
	mkdir -p "$outdir"
	javac --release 17 -encoding UTF-8 -Xlint:-options,-removal -proc:none \
		-cp "$cp" -d "$outdir" check/Smoke.java
	java \
		--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED \
		--add-exports=jdk.compiler/com.sun.source.tree=ALL-UNNAMED \
		-cp "${outdir}:${cp}" Smoke "nullaway_ok ${label}" > "$outdir/out.txt"
	cat "$outdir/out.txt"
	grep -qx "nullaway_ok ${label} NullAway DummyOptionsConfig" "$outdir/out.txt"
}
run_check 0.14.4 %{buildroot}%{_javadir}/nullaway.jar %{buildroot}%{_javadir}/nullaway-annotations.jar %{dataflow_jar} %{plume_jar} "%{reflection_jar}:%{hashmap_jar}" check-new
run_check 0.13.7 %{buildroot}%{_javadir}/nullaway-0.13.7.jar %{buildroot}%{_javadir}/nullaway-annotations-0.13.7.jar %{dataflow_old_jar} %{plume_old_jar} %{plume_old_jar} check-old

%files -f .mfiles
%doc README.md
%license LICENSE.txt
