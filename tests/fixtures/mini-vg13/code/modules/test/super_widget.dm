/obj/test/widget/super
  name = "super widget"
  desc = "A test widget with extra charge."
  charge = 100

  proc/megazap()
    charge -= 10
    return charge
