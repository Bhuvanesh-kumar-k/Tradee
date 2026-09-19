import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/auth_provider.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class TermsAgreementScreen extends StatefulWidget {
  const TermsAgreementScreen({super.key});

  @override
  State<TermsAgreementScreen> createState() => _TermsAgreementScreenState();
}

class _TermsAgreementScreenState extends State<TermsAgreementScreen> {
  String _termsText = 'Loading terms...';
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchTerms();
  }

  Future<void> _fetchTerms() async {
    try {
      final response = await ApiClient.get(Constants.terms);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _termsText = data['terms'] ?? 'Terms not available';
          _isLoading = false;
        });
      } else {
        setState(() {
          _termsText = _getDefaultTerms();
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _termsText = _getDefaultTerms();
        _isLoading = false;
      });
    }
  }

  String _getDefaultTerms() {
    return '''
CRYPTO TRADING PLATFORM - TERMS OF SERVICE & RISK DISCLAIMER

⚠️ HIGH-RISK WARNING: Cryptos and Virtual Digital Assets (VDAs) are highly volatile and unregulated in India. You assume 100% responsibility for your capital and potential losses.

1. ACKNOWLEDGMENT OF RISKS
- Trading cryptocurrencies involves substantial risk of loss
- Past performance is not indicative of future results
- You should only trade with funds you can afford to lose
- The platform is not responsible for any trading losses

2. REGULATORY COMPLIANCE
- Users must comply with all applicable Indian laws
- VDA taxation rules apply as per government regulations
- Users are responsible for their own tax reporting

3. PLATFORM USAGE
- The platform provides tools and signals, not financial advice
- All trading decisions are solely your responsibility
- The platform does not guarantee profits or prevent losses

4. DATA & PRIVACY
- Your data is encrypted and stored securely
- API keys are encrypted at rest
- We do not share your data with third parties

5. LIMITATION OF LIABILITY
- The platform is not liable for any direct or indirect losses
- Technical issues may occur; we are not responsible for downtime
- Market conditions can change rapidly

By clicking "I Understand & Accept All Risks", you acknowledge that you have read, understood, and agree to these terms.
    ''';
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    return PopScope(
      canPop: false,
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        appBar: AppBar(
          title: const Text('Terms & Risk Disclaimer'),
          automaticallyImplyLeading: false,
        ),
        body: SafeArea(
          child: Column(
            children: [
              // Warning Banner
              Container(
                width: double.infinity,
                padding: EdgeInsets.all(16.w),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.1),
                  border: Border.all(color: Colors.red),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning, color: Colors.red, size: 24.sp),
                    SizedBox(width: 12.w),
                    Expanded(
                      child: Text(
                        '⚠️ HIGH-RISK WARNING: Cryptos and Virtual Digital Assets (VDAs) are highly volatile and unregulated in India. You assume 100% responsibility for your capital and potential losses.',
                        style: TextStyle(
                          color: Colors.red,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              
              // Terms Content
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : SingleChildScrollView(
                        padding: EdgeInsets.all(16.w),
                        child: Container(
                          padding: EdgeInsets.all(16.w),
                          decoration: BoxDecoration(
                            color: AppTheme.cardColor,
                            borderRadius: BorderRadius.circular(12.r),
                          ),
                          child: Text(
                            _termsText,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ),
                      ),
              ),
              
              // Action Buttons
              Container(
                padding: EdgeInsets.all(16.w),
                child: Column(
                  children: [
                    SizedBox(
                      width: double.infinity,
                      height: 50.h,
                      child: ElevatedButton(
                        onPressed: authProvider.isLoading
                            ? null
                            : () async {
                                final success = await authProvider.acceptTerms();
                                if (success && mounted) {
                                  Navigator.of(context).popUntil((route) => route.isFirst);
                                }
                              },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryColor,
                        ),
                        child: authProvider.isLoading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('I Understand & Accept All Risks'),
                      ),
                    ),
                    SizedBox(height: 12.h),
                    SizedBox(
                      width: double.infinity,
                      height: 50.h,
                      child: OutlinedButton(
                        onPressed: () {
                          SystemNavigator.pop();
                        },
                        style: OutlinedButton.styleFrom(
                          foregroundColor: Colors.red,
                          side: BorderSide(color: Colors.red),
                        ),
                        child: const Text('I Decline & Exit'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
