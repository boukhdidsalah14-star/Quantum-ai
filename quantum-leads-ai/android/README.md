# Quantum Leads AI for Android

This Android shell opens the live Quantum Leads AI workspace at https://quantum-leads-ai.onrender.com/ inside a native Android WebView. It uses the app's existing Quantum Leads AI logo, supports JavaScript and browser storage needed by the current login, keeps navigation inside the app for the approved Render host, and opens external links in the browser.

## Build

From this directory, with JDK 17 and Gradle 8.9 installed:

```sh
gradle assembleDebug
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`.

The APK is debug-signed for direct personal installation. It is not a Play Store release. The app requires an internet connection and the Render service to be online.
