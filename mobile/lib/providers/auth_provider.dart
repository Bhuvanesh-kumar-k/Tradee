import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';

class AuthProvider with ChangeNotifier {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _errorMessage;
  Map<String, dynamic>? _user;
  
  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  Map<String, dynamic>? get user => _user;
  bool get termsAccepted => _user?['terms_accepted'] == true;
  
  AuthProvider() {
    _checkAuthStatus();
  }
  
  Future<void> _checkAuthStatus() async {
    final token = await _storage.read(key: 'access_token');
    _isAuthenticated = token != null;
    notifyListeners();
  }
  
  Future<bool> requestOtp(String email) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final response = await ApiClient.post(
        Constants.requestOtp,
        body: {'email': email},
      );
      
      if (response.statusCode == 200) {
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _errorMessage = 'Failed to send OTP';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  Future<bool> verifyOtpAndRegister({
    required String email,
    required String otp,
    required String password,
    String? name,
    String? experienceLevel,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final response = await ApiClient.post(
        Constants.verifyOtp,
        body: {
          'email': email,
          'otp_code': otp,
          'password': password,
          if (name != null) 'name': name,
          if (experienceLevel != null) 'experience_level': experienceLevel,
        },
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _storage.write(key: 'access_token', value: data['access_token']);
        _user = data['user'];
        _isAuthenticated = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _errorMessage = 'Invalid OTP or registration failed';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final response = await ApiClient.post(
        Constants.login,
        body: {'email': email, 'password': password},
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _storage.write(key: 'access_token', value: data['access_token']);
        _user = data['user'];
        _isAuthenticated = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _errorMessage = 'Invalid email or password';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
    _isAuthenticated = false;
    _user = null;
    notifyListeners();
  }
  
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  Future<bool> acceptTerms() async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await ApiClient.post(
        Constants.acceptTerms,
        body: {'accepted': true},
      );
      if (response.statusCode == 200) {
        if (_user != null) {
          _user!['terms_accepted'] = true;
        }
        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      _errorMessage = 'Failed to accept terms: $e';
    }
    _isLoading = false;
    notifyListeners();
    return false;
  }
}
