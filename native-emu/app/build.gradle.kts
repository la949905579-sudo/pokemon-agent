plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.dsh.emu"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.dsh.emu"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
        // 决策：P0 只做 arm64
        ndk { abiFilters += listOf("arm64-v8a") }
        externalNativeBuild {
            cmake {
                arguments += listOf("-DANDROID_STL=c++_shared")
            }
        }
    }

    externalNativeBuild {
        cmake { path = file("src/main/cpp/CMakeLists.txt") }
    }

    buildFeatures { compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.15" }

    packaging {
        jniLibs { useLegacyPackaging = false }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation(platform("androidx.compose:compose-bom:2024.09.02"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
