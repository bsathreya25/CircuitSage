from tools import calculate_current, calculate_power

current = calculate_current(5, 220)

print("Current:", current, "A")

power = calculate_power(5, current)

print("Power:", power, "W")