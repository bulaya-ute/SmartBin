import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final bool connected;
  final VoidCallback? onConnectionTap;

  const CustomAppBar({
    super.key,
    required this.connected,
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
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: connected ? Colors.green : Colors.red,
                    boxShadow: [
                      BoxShadow(
                        color: (connected ? Colors.green : Colors.red).withOpacity(0.3),
                        blurRadius: 4,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  connected ? 'Connected' : 'Disconnected',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: connected ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
