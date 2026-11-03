plugins { id("com.android.application") }

android {
    namespace = "pt.saudepratica.linktest"
    compileSdk = 35
    defaultConfig {
        applicationId = "pt.saudepratica.linktest"
        minSdk = 26
        targetSdk = 35
        versionCode = 2
        versionName = "0.2"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
