import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';

class SettingsProvider with ChangeNotifier {
  Map<String, dynamic> _settings = {};
  bool _isLoading = false;
  String? _errorMessage;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
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
      // Save sensitive keys to secure storage
      if (updates.containsKey('coindcx')) {
        final coindcx = updates['coindcx'];
        if (coindcx != null) {
          await _storage.write(key: 'coindcx_api_key', value: coindcx['api_key']);
          await _storage.write(key: 'coindcx_api_secret', value: coindcx['api_secret']);
        }
        updates.remove('coindcx'); // Don't send to backend
      }
      
      if (updates.containsKey('ai')) {
        final ai = updates['ai'];
        if (ai != null && ai['api_key'] != null) {
          await _storage.write(key: 'ai_api_key', value: ai['api_key']);
        }
        if (ai != null && ai['provider'] != null) {
          await _storage.write(key: 'ai_provider', value: ai['provider']);
        }
        updates.remove('ai'); // Don't send full AI object to backend
      }
      
      if (updates.containsKey('telegram')) {
        final telegram = updates['telegram'];
        if (telegram != null) {
          await _storage.write(key: 'telegram_api_id', value: telegram['api_id']);
          await _storage.write(key: 'telegram_api_hash', value: telegram['api_hash']);
        }
        updates.remove('telegram'); // Don't send to backend
      }
      
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
