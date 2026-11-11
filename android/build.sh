#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${ANDROID_JAR:?Set to Android API 35 android.jar}"
: "${BUILD_TOOLS:?Set to the Android build-tools directory}"
: "${SIGN_KEYSTORE:?Set to an Android signing keystore}"
python3 package-mobile.py
mkdir -p build/classes build/dex
"$BUILD_TOOLS/aapt2" compile --dir res -o build/res.zip
"$BUILD_TOOLS/aapt2" link -I "$ANDROID_JAR" --manifest AndroidManifest.xml -A build/assets -o build/resources.apk build/res.zip
if [[ -n "${ECJ_JAR:-}" ]]; then
 java -jar "$ECJ_JAR" -1.8 -proc:none -bootclasspath "$ANDROID_JAR:$BUILD_TOOLS/core-lambda-stubs.jar" -d build/classes StudioActivity.java
else
 javac -source 8 -target 8 -bootclasspath "$ANDROID_JAR:$BUILD_TOOLS/core-lambda-stubs.jar" -d build/classes StudioActivity.java
fi
java -cp "$BUILD_TOOLS/lib/d8.jar" com.android.tools.r8.D8 --lib "$ANDROID_JAR" --min-api 26 --output build/dex build/classes/io/github/jskimlam/panhyeong/*.class
cp build/resources.apk build/unsigned.apk
python3 -c "import zipfile; z=zipfile.ZipFile('build/unsigned.apk','a'); z.write('build/dex/classes.dex','classes.dex'); z.close()"
"$BUILD_TOOLS/zipalign" -f 4 build/unsigned.apk build/aligned.apk
java -jar "$BUILD_TOOLS/lib/apksigner.jar" sign --ks "$SIGN_KEYSTORE" --ks-pass env:SIGN_PASSWORD --out build/Panhyeong-Studio-1.1.apk build/aligned.apk
java -jar "$BUILD_TOOLS/lib/apksigner.jar" verify --verbose build/Panhyeong-Studio-1.1.apk
