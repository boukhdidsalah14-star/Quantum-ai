## Crash Details

**Crash Thread**: `Thread[main,5,main]`  
**Crash Timestamp**: `2026-10-20 21:10:38.452 UTC`  

**Crash Message**:
```
android.os.DeadSystemException
```


### Stacktrace

```
java.lang.RuntimeException: android.os.DeadSystemException
	at android.app.ActivityThread.handleSleeping(ActivityThread.java:4890)
	at android.app.ActivityThread.access$2700(ActivityThread.java:235)
	at android.app.ActivityThread$H.handleMessage(ActivityThread.java:2014)
	at android.os.Handler.dispatchMessage(Handler.java:107)
	at android.os.Looper.loop(Looper.java:225)
	at android.app.ActivityThread.main(ActivityThread.java:7563)
	at java.lang.reflect.Method.invoke(Native Method)
	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:539)
	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:994)
Caused by: android.os.DeadSystemException
	... 9 more

```
##


## Termux App Info

**APP_NAME**: `Termux`  
**PACKAGE_NAME**: `com.termux`  
**VERSION_NAME**: `0.118.3`  
**VERSION_CODE**: `1002`  
**TARGET_SDK**: `28`  
**IS_DEBUGGABLE_BUILD**: `false`  
**SE_PROCESS_CONTEXT**: `u:r:untrusted_app_27:s0:c224,c257,c512,c768`  
**SE_FILE_CONTEXT**: `u:object_r:app_data_file:s0:c224,c257,c512,c768`  
**SE_INFO**: `default:targetSdkVersion=28:complete`  
**APK_RELEASE**: `F-Droid`  
**SIGNING_CERTIFICATE_SHA256_DIGEST**: `228FB2CFE90831C1499EC3CCAF61E96E8E1CE70766B9474672CE427334D41C42`  
##


## Device Info

### Software

**OS_VERSION**: `4.9.190-perf-g726745c074e7`  
**SDK_INT**: `29`  
**RELEASE**: `10`  
**ID**: `QP1A.190711.020`  
**DISPLAY**: `QP1A.190711.020`  
**INCREMENTAL**: `V12.0.18.0.QCTINXM`  
**SECURITY_PATCH**: `2022-07-01`  
**IS_DEBUGGABLE**: `0`  
**IS_TREBLE_ENABLED**: `true`  
**TYPE**: `user`  
**TAGS**: `release-keys`  

### Hardware

**MANUFACTURER**: `Xiaomi`  
**BRAND**: `Redmi`  
**MODEL**: `M2006C3MII`  
**PRODUCT**: `cattail`  
**BOARD**: `cattail`  
**HARDWARE**: `mt6765`  
**DEVICE**: `cattail`  
**SUPPORTED_ABIS**: `armeabi-v7a, armeabi`  
**SUPPORTED_32_BIT_ABIS**: `armeabi-v7a, armeabi`  
**SUPPORTED_64_BIT_ABIS**:   
##
