/obj/test/widget
  name = "widget"
  desc = "A simple test widget."
  var/charge = 0

  proc/zap()
    charge -= 1
    return charge

  proc/attack_self(mob/user)
    user << "You poke the widget."
