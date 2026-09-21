import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto_trading_app/utils/constants.dart';

class ApiClient {
  static const String baseUrl = Constants.apiBaseUrl;
  static const FlutterSecureStorage _storage = FlutterSecureStorage();
  
  static Future<Map<String, String>> _getHeaders() async {
    final token = await _storage.read(key: 'access_token');
    final coindcxKey = await _storage.read(key: 'coindcx_api_key');
    final coindcxSecret = await _storage.read(key: 'coindcx_api_secret');
    final binanceKey = await _storage.read(key: 'binance_api_key');
    final binanceSecret = await _storage.read(key: 'binance_api_secret');
    final binanceTestnet = await _storage.read(key: 'binance_testnet');
    final aiKey = await _storage.read(key: 'ai_api_key');
    final aiProvider = await _storage.read(key: 'ai_provider');
    final telegramApiId = await _storage.read(key: 'telegram_api_id');
    final telegramApiHash = await _storage.read(key: 'telegram_api_hash');

    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
      if (coindcxKey != null) 'XCoinDCXKey': coindcxKey,
      if (coindcxSecret != null) 'XCoinDCXSecret': coindcxSecret,
      if (binanceKey != null) 'XBinanceKey': binanceKey,
      if (binanceSecret != null) 'XBinanceSecret': binanceSecret,
      if (binanceTestnet != null) 'XBinanceTestnet': binanceTestnet,
      if (aiKey != null) 'XAIKey': aiKey,
      if (aiProvider != null) 'XAIProvider': aiProvider,
      if (telegramApiId != null) 'XTelegramApiId': telegramApiId,
      if (telegramApiHash != null) 'XTelegramApiHash': telegramApiHash,
    };
  }
  
  static Future<http.Response> get(String endpoint) async {
    final headers = await _getHeaders();
    return http.get(Uri.parse('$baseUrl$endpoint'), headers: headers);
  }
  
  static Future<http.Response> post(String endpoint, {Map<String, dynamic>? body}) async {
    final headers = await _getHeaders();
    return http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
  }
  
  static Future<http.Response> put(String endpoint, {Map<String, dynamic>? body}) async {
    final headers = await _getHeaders();
    return http.put(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
  }
  
  static Future<http.Response> delete(String endpoint) async {
    final headers = await _getHeaders();
    return http.delete(Uri.parse('$baseUrl$endpoint'), headers: headers);
  }
}
