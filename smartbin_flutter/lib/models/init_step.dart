class InitStep {
  final String description;
  final double weight; // relative weight; progress advances proportionally
  final Future<void> Function() action;

  const InitStep({
    required this.description,
    required this.weight,
    required this.action,
  }) : assert(weight > 0);
}
