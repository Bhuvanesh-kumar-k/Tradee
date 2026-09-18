import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:crypto_trading_app/utils/constants.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class WebSocketService extends ChangeNotifier {
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  bool _isConnected = false;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;
  static const Duration _reconnectDelay = Duration(seconds: 5);

  bool get isConnected => _isConnected;

  Future<void> connect() async {
    if (_isConnected) return;

    final token = await _storage.read(key: 'access_token');
    if (token == null) {
      debugPrint('No token found, cannot connect to WebSocket');
      return;
    }

    try {
      final wsUrl = '${Constants.wsUrl}?token=$token';
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      _isConnected = true;
      _reconnectAttempts = 0;
      notifyListeners();

      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
        cancelOnError: false,
      );

      debugPrint('WebSocket connected');
    } catch (e) {
      debugPrint('WebSocket connection error: $e');
      _scheduleReconnect();
    }
  }

  void _handleMessage(dynamic message) {
    try {
      final data = jsonDecode(message);
      final eventType = data['event_type'] as String?;
      
      debugPrint('WebSocket event: $eventType');

      switch (eventType) {
        case 'trade_update':
          _handleTradeUpdate(data);
          break;
        case 'scanner_log':
          _handleScannerLog(data);
          break;
        case 'signal_alert':
          _handleSignalAlert(data);
          break;
        case 'system_status':
          _handleSystemStatus(data);
          break;
        default:
          debugPrint('Unknown event type: $eventType');
      }
    } catch (e) {
      debugPrint('Error parsing WebSocket message: $e');
    }
  }

  void _handleTradeUpdate(Map<String, dynamic> data) {
    // Notify listeners about trade update
    // This will be handled by TradeProvider
    notifyListeners();
  }

  void _handleScannerLog(Map<String, dynamic> data) {
    // Notify listeners about scanner log
    notifyListeners();
  }

  void _handleSignalAlert(Map<String, dynamic> data) {
    // Notify listeners about signal alert
    notifyListeners();
  }

  void _handleSystemStatus(Map<String, dynamic> data) {
    // Notify listeners about system status
    notifyListeners();
  }

  void _handleError(dynamic error) {
    debugPrint('WebSocket error: $error');
    _isConnected = false;
    notifyListeners();
    _scheduleReconnect();
  }

  void _handleDisconnect() {
    debugPrint('WebSocket disconnected');
    _isConnected = false;
    notifyListeners();
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      debugPrint('Max reconnection attempts reached');
      return;
    }

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(_reconnectDelay, () {
      _reconnectAttempts++;
      debugPrint('Reconnection attempt $_reconnectAttempts');
      connect();
    });
  }

  void disconnect() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    _isConnected = false;
    notifyListeners();
    debugPrint('WebSocket disconnected manually');
  }

  void resetReconnectAttempts() {
    _reconnectAttempts = 0;
  }
}
