import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';

class SettingsProvider with ChangeNotifier {
  Map<String, dynamic> _settings = {};
  bool _isLoading = false;
  String? _errorMessage;
  
  Map<String, dynamic> get settings => _settings;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  
  Future<void> fetchSettings() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.get(Constants.settings);
      
      if (response.statusCode == 200) {
        _settings = jsonDecode(response.body);
        _isLoading = false;
        notifyListeners();
      } else {
        _errorMessage = 'Failed to fetch settings';
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<bool> updateSettings(Map<String, dynamic> updates) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.put(
        Constants.settings,
        body: updates,
      );
      
      if (response.statusCode == 200) {
        await fetchSettings();
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _errorMessage = 'Failed to update settings';
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
  
  Future<bool> verifyAiKey(String provider, String apiKey) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.post(
        Constants.verifyAiKey,
        body: {'provider': provider, 'api_key': apiKey},
      );
      
      if (response.statusCode == 200) {
        await fetchSettings();
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _errorMessage = 'Failed to verify AI key';
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
  
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
