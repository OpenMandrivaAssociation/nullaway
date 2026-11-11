Name:		nullaway
Version:	0.13.7
Release:	1
Summary:	Error Prone checker for nullness
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/uber/NullAway
# Tag v0.13.7 with the Gradle wrapper jar removed.
Source0:	nullaway-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(com.google.errorprone:error_prone_check_api) = 2.50.0
BuildRequires:	mvn(com.google.errorprone:error_prone_annotation) = 2.50.0
BuildRequires:	mvn(org.checkerframework:dataflow-nullaway) = 4.0.0
BuildRequires:	mvn(com.google.guava:guava) = 33.6.0-jre
BuildRequires:	mvn(org.jspecify:jspecify) = 1.0.0
BuildRequires:	mvn(org.jetbrains:annotations)
BuildRequires:	mvn(javax.inject:javax.inject) = 1.0.5
BuildRequires:	mvn(com.google.code.findbugs:jsr305) = 3.0.2
BuildRequires:	mvn(com.google.auto.service:auto-service-annotations) = 1.1.1
BuildRequires:	mvn(org.plumelib:plume-util) = 1.8.1
BuildRequires:	mvn(org.checkerframework:checker-qual) = 4.4.0
Requires:	mvn(com.uber.nullaway:nullaway-annotations) = %{version}
Requires:	mvn(com.google.errorprone:error_prone_check_api) = 2.50.0
Requires:	mvn(com.google.errorprone:error_prone_annotation) = 2.50.0
Requires:	mvn(org.checkerframework:dataflow-nullaway) = 4.0.0
Requires:	mvn(com.google.guava:guava) = 33.6.0-jre
Requires:	mvn(org.jspecify:jspecify) = 1.0.0
Requires:	mvn(javax.inject:javax.inject) = 1.0.5
Requires:	mvn(com.google.code.findbugs:jsr305) = 3.0.2
Requires:	mvn(org.plumelib:plume-util) = 1.8.1
Requires:	mvn(org.checkerframework:checker-qual) = 4.4.0

%description
NullAway %{version} is the Error Prone nullness checker Gradle 9.9.1
asks the build for. The checker and its annotation jar are compiled
with javac. Dataflow comes from dataflow-nullaway, whose packages are
org.checkerframework.nullaway.dataflow and javacutil. The eisop
dataflow jar is not on the classpath. AutoService is not run. The
BugChecker service file lists NullAway and RequireExplicitNullMarking.

%prep
%autosetup -n NullAway-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
SYS=%{_javadir}
for jar in \
	error_prone_check_api.jar \
	error_prone_annotation.jar \
	dataflow-nullaway.jar \
	guava.jar \
	jspecify.jar \
	org.jetbrains.annotations.jar \
	atinject.jar \
	javax.annotation.jar \
	auto-service-annotations.jar \
	plume-util.jar \
	checker-qual.jar
do
	test -s "$SYS/$jar"
done
flow=$(jar --describe-module --file "$SYS/dataflow-nullaway.jar")
if ! printf '%%s\n' "$flow" | grep -F -q 'org.checkerframework.nullaway'; then
	printf '%%s\n' "$flow"
	exit 1
fi
if printf '%%s\n' "$flow" | grep -F -q 'org.checkerframework.dataflow@'; then
	printf '%%s\n' "$flow"
	exit 1
fi

mkdir -p classes/annotations
find annotations/src/main/java -name '*.java' > annotations.list
test "$(wc -l < annotations.list)" -eq 8
javac --release 11 -encoding UTF-8 -Xlint:-options,-removal -proc:none \
	-d classes/annotations @annotations.list
javap -v -classpath classes/annotations com.uber.nullaway.annotations.Initializer | grep -F -q 'major version: 55'
jar cf nullaway-annotations.jar -C classes/annotations .
jar i nullaway-annotations.jar

mkdir -p classes/nullaway
find nullaway/src/main/java -name '*.java' > nullaway.list
test "$(wc -l < nullaway.list)" -eq 113
CP="nullaway-annotations.jar:$SYS/auto-service-annotations.jar:$SYS/jspecify.jar:$SYS/org.jetbrains.annotations.jar:$SYS/atinject.jar:$SYS/error_prone_annotation.jar:$SYS/error_prone_check_api.jar:$SYS/dataflow-nullaway.jar:$SYS/guava.jar:$SYS/checker-qual.jar:$SYS/javax.annotation.jar:$SYS/plume-util.jar"
javac -encoding UTF-8 -Xlint:-options,-removal -proc:none \
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
	-cp "$CP" -d classes/nullaway @nullaway.list
mkdir -p classes/nullaway/META-INF/services
printf '%%s\n' \
	com.uber.nullaway.NullAway \
	com.uber.nullaway.RequireExplicitNullMarking \
	> classes/nullaway/META-INF/services/com.google.errorprone.bugpatterns.BugChecker
jar cf nullaway.jar -C classes/nullaway .
jar i nullaway.jar
javap -v -classpath nullaway.jar com.uber.nullaway.NullAway | grep -F -q 'major version: 71'
jar tf nullaway.jar | grep -F -q 'META-INF/services/com.google.errorprone.bugpatterns.BugChecker'
desc=$(jar --describe-module --file nullaway.jar)
if printf '%%s\n' "$desc" | grep -F -q 'Unable'; then
	printf '%%s\n' "$desc"
	exit 1
fi

write_pom() {
	file=$1
	artifact=$2
	deps=$3
	cat > "$file" <<END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.uber.nullaway</groupId>
  <artifactId>$artifact</artifactId>
  <version>%{version}</version>
  <name>$artifact</name>
  <description>NullAway $artifact %{version}.</description>
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
{
	printf '%%s\n' '  <dependencies>'
	req_dep com.uber.nullaway nullaway-annotations %{version}
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
} > nullaway.deps
write_pom nullaway-annotations.pom nullaway-annotations ''
write_pom nullaway.pom nullaway "$(cat nullaway.deps)"
grep -F -q '<version>%{version}</version>' nullaway.pom
grep -F -q '<artifactId>dataflow-nullaway</artifactId>' nullaway.pom
if grep -F -q 'eisop' nullaway.pom; then
	exit 1
fi

%install
set -eo pipefail
: > .mfiles
pin_side() {
	mod=$1
	sysjar install --buildroot %{buildroot} \
		--artifact "$mod.pom:$mod.jar" \
		--file-name "$mod-%{version}" \
		--filelist ".mfiles-$mod"
	index="%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${mod}.sysjar"
	test -f "$index"
	/bin/mv "$index" "%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${mod}-%{version}.sysjar"
	sed -i "s|/usr/share/sysjar/index/com\\.uber\\.nullaway/${mod}\\.sysjar|/usr/share/sysjar/index/com.uber.nullaway/${mod}-%{version}.sysjar|" ".mfiles-$mod"
	grep -F -q '"version": "%{version}"' "%{buildroot}/usr/share/sysjar/index/com.uber.nullaway/${mod}-%{version}.sysjar"
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
	done < ".mfiles-$mod"
}
pin_side nullaway-annotations
pin_side nullaway
grep -F -q 'nullaway-%{version}.jar' .mfiles
if grep -E -q '/nullaway(-annotations)?\.sysjar$' .mfiles; then
	exit 1
fi

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
SYS=%{_javadir}
JUP=%{buildroot}%{_javadir}
test -s "$JUP/nullaway-%{version}.jar"
test -s "$JUP/nullaway-annotations-%{version}.jar"
CP="$JUP/nullaway-%{version}.jar:$JUP/nullaway-annotations-%{version}.jar:$SYS/error_prone_check_api.jar:$SYS/error_prone_annotation.jar:$SYS/dataflow-nullaway.jar:$SYS/guava.jar:$SYS/jspecify.jar:$SYS/atinject.jar:$SYS/javax.annotation.jar:$SYS/plume-util.jar:$SYS/checker-qual.jar:$SYS/org.jetbrains.annotations.jar"
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
javac --release 17 -encoding UTF-8 -Xlint:-options,-removal -proc:none \
	-cp "$CP" -d check check/Smoke.java
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
	-cp "check:$CP" Smoke nullaway_ok > check.log
cat check.log
grep -qx 'nullaway_ok NullAway DummyOptionsConfig' check.log

%files -f .mfiles
%doc README.md
%license LICENSE.txt
