import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';

class ScannerLog {
  final int id;
  final String coinPair;
  final String timeframe;
  final String? trendStatus;
  final String? signalDetected;
  final DateTime scanTime;
  final Map<String, dynamic>? indicatorValues;
  
  ScannerLog({
    required this.id,
    required this.coinPair,
    required this.timeframe,
    this.trendStatus,
    this.signalDetected,
    required this.scanTime,
    this.indicatorValues,
  });
  
  factory ScannerLog.fromJson(Map<String, dynamic> json) {
    return ScannerLog(
      id: json['id'],
      coinPair: json['coin_pair'],
      timeframe: json['timeframe'],
      trendStatus: json['trend_status'],
      signalDetected: json['signal_detected'],
      scanTime: DateTime.parse(json['scan_time']),
      indicatorValues: json['indicator_values'],
    );
  }
}

class ScannerProvider with ChangeNotifier {
  Map<String, dynamic> _status = {};
  List<ScannerLog> _logs = [];
  bool _isLoading = false;
  String? _errorMessage;
  
  Map<String, dynamic> get status => _status;
  List<ScannerLog> get logs => _logs;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  
  Future<void> fetchStatus() async {
    try {
      final response = await ApiClient.get(Constants.scannerStatus);
      
      if (response.statusCode == 200) {
        _status = jsonDecode(response.body);
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Failed to fetch scanner status';
      notifyListeners();
    }
  }
  
  Future<void> fetchLogs() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.get('${Constants.scannerLogs}?limit=50');
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        _logs = data.map((json) => ScannerLog.fromJson(json)).toList();
        _isLoading = false;
        notifyListeners();
      } else {
        _errorMessage = 'Failed to fetch scanner logs';
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<Map<String, dynamic>?> checkCoin(String coinPair) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.post(
        Constants.checkCoin,
        body: {'coin_pair': coinPair},
      );
      
      if (response.statusCode == 200) {
        _isLoading = false;
        final result = jsonDecode(response.body);
        notifyListeners();
        return result;
      } else {
        _errorMessage = 'Failed to check coin';
        _isLoading = false;
        notifyListeners();
        return null;
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }
  
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
