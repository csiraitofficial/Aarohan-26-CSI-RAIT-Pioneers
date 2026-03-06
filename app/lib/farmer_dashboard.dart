import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:pashu_arogya_app/page2.dart';
import 'package:pashu_arogya_app/treatment.dart';
import '../services/token_storage.dart';
import 'animal_feature.dart';
import '../services/api_config.dart';


class FarmerDashboard extends StatefulWidget {
  const FarmerDashboard({super.key});

  @override
  State<FarmerDashboard> createState() => _FarmerDashboardState();
}

class _FarmerDashboardState extends State<FarmerDashboard> {
<<<<<<< HEAD
  final String baseUrl = ApiConfig.baseUrl;
=======
  // final String baseUrl = "http://10.49.235.7:5000";
  final String baseUrl = "http://192.168.1.206:5000";
>>>>>>> 9a6e891ad6fbd7555b9e02f30ece2891709ec276

  // 🔐 FORCE LOGOUT (used when farmer deleted)
  Future<void> forceLogout() async {
    await TokenStorage.clearToken();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const NextPage()),
          (route) => false,
    );
  }

  // ✅ FETCH PROFILE
  Future<void> fetchProfile() async {
    final token = await TokenStorage.getToken();

    if (token == null) {
      await forceLogout();
      return;
    }

    try {
      final response = await http.get(
        Uri.parse("$baseUrl/auth/me"),
        headers: {
          "Authorization": "Bearer $token",
        },
      );

      final decoded = jsonDecode(response.body);

      if (decoded["status"] == "error") {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("❌ Account not found. Logging out.")),
        );
        await forceLogout();
        return;
      }

      final profile = decoded["data"] is String
          ? jsonDecode(decoded["data"])
          : decoded["data"];

      showProfileDialog(profile);
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("❌ Error loading profile")),
      );
    }
  }

  // 🚪 LOGOUT
  Future<void> logout() async {
    await TokenStorage.clearToken();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const NextPage()),
          (route) => false,
    );
  }

  // 👤 PROFILE DIALOG
  void showProfileDialog(Map<String, dynamic> profile) {
    showDialog(
      context: context,
      builder: (_) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [

                Align(
                  alignment: Alignment.topRight,
                  child: InkWell(
                    onTap: () => Navigator.pop(context),
                    child: const Icon(Icons.close, color: Colors.red),
                  ),
                ),

                const SizedBox(height: 10),

                Text("👤 Name: ${profile["name"] ?? "-"}"),
                Text("🎂 Age: ${profile["age"] ?? "-"}"),
                Text("⚧ Gender: ${profile["gender"] ?? "-"}"),
                Text("🏠 Address: ${profile["address"] ?? "-"}"),

                const SizedBox(height: 10),

                if (profile["gps_location"] != null)
                  Text(
                    "📍 GPS: ${profile["gps_location"]["lat"]}, "
                        "${profile["gps_location"]["lng"]}",
                  ),

                const SizedBox(height: 20),

                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.logout, color: Colors.white),
                    label: const Text(
                      "LOGOUT",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.redAccent,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed: () {
                      Navigator.pop(context);
                      logout();
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // 🟧 BIG VERTICAL IMAGE BUTTON
  // 🟧 BIG VERTICAL IMAGE BUTTON (CENTERED)
  Widget verticalImageButton(
      String label,
      String imagePath,
      VoidCallback onTap,
      ) {
    return InkWell(
      onTap: onTap,
      child: SizedBox(
        width: 280, // ✅ FIXED WIDTH → CENTERED
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 12),
          height: 140,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: const LinearGradient(
              colors: [
                Color(0xFF2E7D32),
                Color(0xFFFF6F00),
              ],
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(
                imagePath,
                height: 70,
                width: 70,
                fit: BoxFit.contain,
              ),
              const SizedBox(height: 10),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  // 🧱 UI
  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async => true,
      child: Scaffold(
        backgroundColor: const Color(0xFFFFF8E1),

        appBar: AppBar(
          backgroundColor: const Color(0xFFFF6F00),
          title: const Text("Farmer Dashboard"),
          centerTitle: true,
          foregroundColor: Colors.white,
          leading: IconButton(
            icon: const Icon(Icons.person),
            onPressed: fetchProfile,
          ),
        ),

        body: Padding(
          padding: const EdgeInsets.all(20),
          child: Center( // ✅ ADD THIS
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center, // ✅ ADD THIS
              children: [

                const SizedBox(height: 20),

                verticalImageButton(
                  "Treatment",
                  "assets/images/treatment.png",
                      () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const TreatmentPage()),
                    );
                  },
                ),


                verticalImageButton(
                  "Animal",
                  "assets/images/animal.png",
                      () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const AnimalFeaturePage(),
                      ),
                    );
                  },
                ),


                verticalImageButton(
                  "Prescription",
                  "assets/images/presc.png",
                      () {
                    print("Prescription Clicked");
                  },
                ),
              ],
            ),
          ),
        ),

      ),
    );
  }
}
