plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    signingConfigs {
        create("fixed") {
            storeFile = file("keystore.jks")
            storePassword = "emu123456"
            keyAlias = "emu"
            keyPassword = "emu123456"
        }
    }
    buildFeatures {
        buildConfig = true
    }
    buildTypes {
        debug { signingConfig = signingConfigs.getByName("fixed") }
    }
    namespace = "com.dsh.emu"
    compileSdk = 34
    ndkVersion = "27.0.12077973"

    defaultConfig {
        applicationId = "com.dsh.emu"
        minSdk = 26
        targetSdk = 34
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toIntOrNull() ?: 1
        versionName = "0.2"
        buildConfigField("String", "GIT_SHA", "\"${(System.getenv("GITHUB_SHA") ?: "local").take(7)}\"")
        buildConfigField("String", "BUILD_TIME", "\"${System.currentTimeMillis()}\"")
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

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

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

// 构建前给 mGBA 插调试日志（定位 core->init 崩溃用）
tasks.register("patchMgba") {
    doLast {
        val root = project.rootDir
        val proc = ProcessBuilder("python3", "$root/tools/patch_mgba.py")
            .directory(root)
            .redirectErrorStream(true)
            .start()
        val out = proc.inputStream.bufferedReader().readText()
        val rc = proc.waitFor()
        println("patchMgba rc=$rc out=$out")
    }
}
tasks.named("preBuild") { dependsOn("patchMgba") }
