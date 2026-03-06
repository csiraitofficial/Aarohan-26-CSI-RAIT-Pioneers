import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

import 'FarmerRegistrationForm.dart';
import 'farmer_dashboard.dart';
import 'package:pashu_arogya_app/services/token_storage.dart';

import '../services/api_config.dart';


class FarmerForm extends StatefulWidget {
  const FarmerForm({super.key});

  @override
  State<FarmerForm> createState() => _FarmerFormState();
}

class _FarmerFormState extends State<FarmerForm>
    with SingleTickerProviderStateMixin {

  late AnimationController _controller;
  late Animation<double> fadeAnim;

  final TextEditingController mobileController = TextEditingController();
  final TextEditingController otpController = TextEditingController();

  bool showOtpField = false;
  bool loading = false;
  String apiResponse = "";

<<<<<<< HEAD
  final String baseUrl = ApiConfig.baseUrl;
=======
  // ✅ ✅ ✅ YOUR CORRECT SERVER IP + PORT
  // final String baseUrl = "http://10.49.235.7:5000";
  final String baseUrl = "http://192.168.1.206:5000";
>>>>>>> 9a6e891ad6fbd7555b9e02f30ece2891709ec276

  @override
  void initState() {
    super.initState();
    _controller =
        AnimationController(vsync: this, duration: const Duration(milliseconds: 900));
    fadeAnim = CurvedAnimation(parent: _controller, curve: Curves.easeIn);
    _controller.forward();
  }

  // ================== NEW USER SEND OTP ==================
  Future<void> sendOtp() async {
    if (mobileController.text.length != 10) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text("Enter valid 10 digit mobile")));
      return;
    }

    setState(() => loading = true);

    try {
      final response = await http.post(
        Uri.parse("$baseUrl/auth/send-otp"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"mobile": mobileController.text}),
      );

      setState(() {
        showOtpField = true;
        loading = false;
        apiResponse = response.body;
      });
    } catch (e) {
      setState(() {
        loading = false;
        apiResponse = "❌ Server error";
      });
    }
  }

  // ================== NEW USER VERIFY OTP ==================
  Future<void> verifyOtp() async {
    if (otpController.text.length != 6) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text("Enter valid 6 digit OTP")));
      return;
    }

    setState(() => loading = true);

    try {
      final response = await http.post(
        Uri.parse("$baseUrl/auth/verify-otp"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "mobile": mobileController.text,
          "otp_code": otpController.text,
        }),
      );

      final decoded = jsonDecode(response.body);

      setState(() {
        loading = false;
        apiResponse = response.body;
      });

      if (decoded["status"] == "success") {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) =>
                FarmerRegistrationForm(tempToken: decoded["data"]["temp_token"]),
          ),
        );
      } else {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text("❌ OTP verification failed")));
      }
    } catch (e) {
      setState(() => loading = false);
    }
  }

  // ================== LOGIN DIALOG ==================
  void showLoginDialog() {
    final TextEditingController loginMobileController = TextEditingController();
    final TextEditingController loginOtpController = TextEditingController();

    bool otpSent = false;
    bool dialogLoading = false;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return Dialog(
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [

                    Align(
                      alignment: Alignment.topRight,
                      child: InkWell(
                        onTap: () => Navigator.pop(dialogContext),
                        child: const Icon(Icons.close, color: Colors.red),
                      ),
                    ),

                    const Text(
                      "Login",
                      style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2E7D32)),
                    ),

                    const SizedBox(height: 16),

                    TextField(
                      controller: loginMobileController,
                      keyboardType: TextInputType.number,
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                        LengthLimitingTextInputFormatter(10),
                      ],
                      decoration: _fieldDecoration("Mobile Number"),
                    ),

                    const SizedBox(height: 12),

                    if (otpSent)
                      TextField(
                        controller: loginOtpController,
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly,
                          LengthLimitingTextInputFormatter(6),
                        ],
                        decoration: _fieldDecoration("Enter OTP"),
                      ),

                    const SizedBox(height: 20),

                    InkWell(
                      onTap: dialogLoading
                          ? null
                          : () async {
                        if (loginMobileController.text.length != 10) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text("Enter valid mobile")),
                          );
                          return;
                        }

                        setDialogState(() => dialogLoading = true);

                        // SEND OTP
                        if (!otpSent) {
                          await http.post(
                            Uri.parse("$baseUrl/auth/login"),
                            headers: {"Content-Type": "application/json"},
                            body: jsonEncode({
                              "mobile": loginMobileController.text
                            }),
                          );

                          setDialogState(() {
                            otpSent = true;
                            dialogLoading = false;
                          });
                          return;
                        }

                        // LOGIN
                        final response = await http.post(
                          Uri.parse(
                              "$baseUrl/auth/verify-otp-and-login"),
                          headers: {"Content-Type": "application/json"},
                          body: jsonEncode({
                            "mobile": loginMobileController.text,
                            "otp_code": loginOtpController.text,
                          }),
                        );

                        final decoded =
                        jsonDecode(response.body);

                        setDialogState(() => dialogLoading = false);

                        if (decoded["status"] == "success") {
                          await TokenStorage.saveToken(
                              decoded["data"]["access_token"]);

                          Navigator.pop(dialogContext);

                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                                builder: (_) =>
                                const FarmerDashboard()),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text("❌ Login failed")),
                          );
                        }
                      },
                      child: Container(
                        height: 50,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(14),
                          gradient: const LinearGradient(
                            colors: [
                              Color(0xFF2E7D32),
                              Color(0xFFFF6F00),
                            ],
                          ),
                        ),
                        child: Center(
                          child: dialogLoading
                              ? const CircularProgressIndicator(
                              color: Colors.white)
                              : Text(
                            otpSent ? "LOGIN" : "GET OTP",
                            style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  // ================== UI ==================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        backgroundColor: const Color(0xFFFF6F00),
        title: const Text("Farmer Mobile Verification"),
        centerTitle: true,
        foregroundColor: Colors.white,
      ),
      body: FadeTransition(
        opacity: fadeAnim,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: ListView(
            children: [

              _title("Enter Mobile Number"),

              TextField(
                controller: mobileController,
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(10),
                ],
                decoration: _fieldDecoration("Mobile Number"),
              ),

              const SizedBox(height: 20),

              if (showOtpField) ...[
                _title("Enter OTP"),
                TextField(
                  controller: otpController,
                  keyboardType: TextInputType.number,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                    LengthLimitingTextInputFormatter(6),
                  ],
                  decoration: _fieldDecoration("6 Digit OTP"),
                ),
                const SizedBox(height: 20),
              ],

              InkWell(
                onTap: loading ? null : showOtpField ? verifyOtp : sendOtp,
                child: _mainButton(showOtpField ? "VERIFY OTP" : "GET OTP"),
              ),

              const SizedBox(height: 12),

              InkWell(
                onTap: showLoginDialog,
                child: _mainButton("Already have an account?"),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ================== HELPERS ==================
  Widget _mainButton(String text) {
    return Container(
      height: 55,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        gradient: const LinearGradient(
          colors: [Color(0xFF2E7D32), Color(0xFFFF6F00)],
        ),
      ),
      child: Center(
        child: loading
            ? const CircularProgressIndicator(color: Colors.white)
            : Text(
          text,
          style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  Widget _title(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(text,
        style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF2E7D32))),
  );

  InputDecoration _fieldDecoration(String label) => InputDecoration(
    filled: true,
    fillColor: Colors.white,
    labelText: label,
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
  );
}
