import 'package:flutter/material.dart' hide ConnectionState;
import '../screens/home_screen.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final ConnectionState connectionState;
  final VoidCallback? onConnectionTap;

  const CustomAppBar({
    super.key,
    required this.connectionState,
    this.onConnectionTap,
  });

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: const Text('📱 SmartBin Control'),
      elevation: 2,
      actions: [
        // Connection status indicator
        Padding(
          padding: const EdgeInsets.only(right: 16.0),
          child: GestureDetector(
            onTap: onConnectionTap,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildConnectionIndicator(),
                const SizedBox(width: 8),
                Text(
                  _getConnectionText(),
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: _getConnectionColor(),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildConnectionIndicator() {
    switch (connectionState) {
      case ConnectionState.connected:
        return Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.green,
            boxShadow: [
              BoxShadow(
                color: Colors.green.withOpacity(0.3),
                blurRadius: 4,
                spreadRadius: 1,
              ),
            ],
          ),
        );

      case ConnectionState.connecting:
        return SizedBox(
          width: 12,
          height: 12,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.orange),
          ),
        );

      case ConnectionState.disconnected:
      default:
        return Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.red,
            boxShadow: [
              BoxShadow(
                color: Colors.red.withOpacity(0.3),
                blurRadius: 4,
                spreadRadius: 1,
              ),
            ],
          ),
        );
    }
  }

  String _getConnectionText() {
    switch (connectionState) {
      case ConnectionState.connected:
        return 'Connected';
      case ConnectionState.connecting:
        return 'Connecting...';
      case ConnectionState.disconnected:
      default:
        return 'Disconnected';
    }
  }

  Color _getConnectionColor() {
    switch (connectionState) {
      case ConnectionState.connected:
        return Colors.green;
      case ConnectionState.connecting:
        return Colors.orange;
      case ConnectionState.disconnected:
      default:
        return Colors.red;
    }
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
