import 'package:flutter/material.dart';
import 'package:pashu_arogya_app/services/token_storage.dart';
import 'dart:async';
import 'farmer_dashboard.dart';
import 'page2.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: SplashScreen(), // ✅ ALWAYS SHOW SPLASH FIRST
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {

  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );

    _animation = Tween<double>(begin: 80, end: 200)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    // ✅ PRELOAD IMAGE & START ANIMATION
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await precacheImage(
        const AssetImage("assets/images/pashulogoe.png"),
        context,
      );
      _controller.forward();
    });

    // ✅ AFTER 3 SECONDS → CHECK TOKEN & REDIRECT
    Timer(const Duration(seconds: 3), () async {
      final token = await TokenStorage.getToken();

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) =>
          token == null ? const NextPage() : const FarmerDashboard(),
        ),
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: AnimatedBuilder(
          animation: _animation,
          builder: (context, child) {
            return SizedBox(
              height: _animation.value,
              width: _animation.value,
              child: Image.asset("assets/images/pashulogoe.png"),
            );
          },
        ),
      ),
    );
  }
}
