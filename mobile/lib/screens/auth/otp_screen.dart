import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/auth_provider.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class OtpScreen extends StatefulWidget {
  final String email;
  final String password;
  
  const OtpScreen({
    super.key,
    required this.email,
    required this.password,
  });

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final _otpController = TextEditingController();
  final _nameController = TextEditingController();
  String? _experienceLevel;
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _otpController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _handleVerify() async {
    if (!_formKey.currentState!.validate()) return;

    final authProvider = context.read<AuthProvider>();
    
    final nameVal = _nameController.text.trim();
    final success = await authProvider.verifyOtpAndRegister(
      email: widget.email,
      otp: _otpController.text.trim(),
      password: widget.password,
      name: nameVal.isEmpty ? null : nameVal,
      experienceLevel: _experienceLevel,
    );
    
    if (success && mounted) {
      // Pop all pushed auth screens back to the root AuthWrapper
      Navigator.of(context).popUntil((route) => route.isFirst);
    } else if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authProvider.errorMessage ?? 'Verification failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Verify Email'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(horizontal: 24.w),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SizedBox(height: 32.h),
                Icon(
                  Icons.verified_user_outlined,
                  size: 64.sp,
                  color: AppTheme.primaryColor,
                ),
                SizedBox(height: 24.h),
                Text(
                  'Enter OTP sent to ${widget.email}',
                  style: Theme.of(context).textTheme.titleLarge,
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 32.h),
                TextFormField(
                  controller: _otpController,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  decoration: const InputDecoration(
                    labelText: 'OTP Code',
                    prefixIcon: Icon(Icons.sms_outlined),
                    counterText: '',
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter OTP';
                    }
                    if (value.length != 6) {
                      return 'OTP must be 6 digits';
                    }
                    return null;
                  },
                ),
                SizedBox(height: 16.h),
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Your Name (Optional)',
                    prefixIcon: Icon(Icons.person_outlined),
                  ),
                ),
                SizedBox(height: 16.h),
                DropdownButtonFormField<String>(
                  value: _experienceLevel,
                  decoration: const InputDecoration(
                    labelText: 'Experience Level',
                    prefixIcon: Icon(Icons.trending_up),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'Beginner', child: Text('Beginner')),
                    DropdownMenuItem(value: 'Intermediate', child: Text('Intermediate')),
                    DropdownMenuItem(value: 'Pro', child: Text('Pro')),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _experienceLevel = value;
                    });
                  },
                ),
                SizedBox(height: 32.h),
                ElevatedButton(
                  onPressed: authProvider.isLoading ? null : _handleVerify,
                  child: authProvider.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Verify & Register'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
