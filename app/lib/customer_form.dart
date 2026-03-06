import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../services/api_config.dart';

class CustomerForm extends StatefulWidget {
  const CustomerForm({super.key});

  @override
  State<CustomerForm> createState() => _CustomerFormState();
}

class _CustomerFormState extends State<CustomerForm>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> fadeAnim;

  final TextEditingController farmerIdCtrl = TextEditingController();
  bool loading = false;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );

    fadeAnim = CurvedAnimation(parent: _controller, curve: Curves.easeIn);
    _controller.forward();
  }

  // ================= INFO ROW =================
  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              "$label:",
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  // ================= SHOW RESULT DIALOG =================
  void showSafetyDialog(Map data) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Consumer Safety Check"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _infoRow("Status", data["status"]),
            _infoRow("Message", data["message"]),
            if (data["safe_after"] != null)
              _infoRow("Safe After", data["safe_after"]),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("OK"),
          )
        ],
      ),
    );
  }

  // ================= API CALL =================
  Future<void> checkConsumerSafety() async {
    final farmerId = farmerIdCtrl.text.trim();

    if (farmerId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("⚠️ Please enter Farmer ID")),
      );
      return;
    }

    setState(() => loading = true);

    final url = "${ApiConfig.baseUrl}/consumer/safety/$farmerId";

    try {
      final res = await http.get(Uri.parse(url));

      setState(() => loading = false);

      // ✅ PRINT RAW JSON
      debugPrint("🔵 Consumer Safety API raw response:");
      debugPrint(res.body);

      final decoded = jsonDecode(res.body);

      // ❌ Error case
      if (decoded["status"] != "success") {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(decoded["message"] ?? "❌ Failed")),
        );
        return;
      }

      final Map data = decoded["data"];

      showSafetyDialog(data);
    } catch (e) {
      setState(() => loading = false);

      debugPrint("❌ API ERROR: $e");

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("❌ Server not reachable")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        backgroundColor: const Color(0xFFFF6F00),
        title: const Text("Customer Verification"),
        centerTitle: true,
        foregroundColor: Colors.white,
      ),
      body: FadeTransition(
        opacity: fadeAnim,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: ListView(
            children: [
              TextField(
                controller: farmerIdCtrl,
                decoration: InputDecoration(
                  filled: true,
                  fillColor: Colors.white,
                  labelText: "Enter Farmer ID",
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),

              const SizedBox(height: 24),

              ElevatedButton.icon(
                onPressed: loading ? null : checkConsumerSafety,
                icon: loading
                    ? const SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
                    : const Icon(Icons.verified),
                label: const Text("CHECK SAFETY"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF5AAD5E),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),

              const SizedBox(height: 30),


            ],
          ),
        ),
      ),
    );
  }
}
