# Termux Screen Stream

Architecture:

Android APK (MediaProjection) -> `127.0.0.1:8765` -> Termux Python server -> browser `http://127.0.0.1:8080`

The APK asks Android for screen-capture permission. Termux does not bypass Android's permission system.

## 1. Termux

Install Termux from a trusted/current source, then:

```sh
pkg update
pkg install python
cd ~/termux-screen-stream/server
python server.py
```

The server listens on:
- ingest: `127.0.0.1:8765`
- browser: `0.0.0.0:8080`

Open:

```text
http://127.0.0.1:8080
```

## 2. Build the APK

This project is an Android Studio/Gradle project.

Open the `android` directory in Android Studio and build the debug APK, or from a machine with Gradle/Android SDK:

```sh
cd android
./gradlew assembleDebug
```

The APK will be:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

Install it on the same Android phone running Termux.

## 3. Start streaming

1. Start `python server.py` in Termux.
2. Open the Screen Stream app.
3. Tap **Start screen sharing**.
4. Android displays its screen-capture confirmation dialog.
5. Approve it.
6. Open `http://127.0.0.1:8080` in the phone browser.

The browser shows the latest JPEG frames as an MJPEG stream.

## Notes

- This is intended for your own device or devices you are authorized to control.
- The user must explicitly grant Android screen-capture permission.
- Stop sharing from the app notification/Stop button.
- This first version is local-only. A later version can put the browser endpoint behind Cloudflare Tunnel.
