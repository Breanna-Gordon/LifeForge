# Normal life events — five per stage now instead of three, so the same
# three prompts don't repeat constantly across a playthrough.
choice_events = {
    "Baby": {
        "choices": {
            "Your parent wants you to try a new food.": {
                "Try it": {"physical": 2, "mental": 1, "social": 1},
                "Refuse": {"physical": -1, "mental": 1, "social": -1}
            },
            "You are given a favourite toy.": {
                "Play with it": {"mental": 2, "social": 1},
                "Ignore it": {"mental": -1, "social": -1}
            },
            "You have a chance to interact with another child.": {
                "Interact": {"social": 3, "mental": 1},
                "Stay alone": {"social": -2, "mental": -1}
            },
            "You take your first steps.": {
                "Keep trying": {"physical": 3, "mental": 1},
                "Cry instead": {"physical": -1, "social": -1}
            },
            "A loud noise startles you.": {
                "Cling to a parent": {"social": 2, "mental": 1},
                "Explore anyway": {"physical": 1, "mental": -1}
            }
        }
    },

    "Childhood": {
        "choices": {
            "You are invited to join an after-school activity.": {
                "Join": {"physical": 2, "social": 3, "mental": 1},
                "Stay home": {"social": -1, "mental": 1}
            },
            "You have homework due tomorrow.": {
                "Do the homework": {"mental": 3, "social": -1},
                "Leave it": {"mental": -2, "social": 1}
            },
            "Your friend asks you to play outside.": {
                "Go outside": {"physical": 3, "social": 2},
                "Stay inside": {"physical": -1, "mental": 1}
            },
            "You get picked last for a team.": {
                "Shrug it off": {"mental": 1, "social": 1},
                "Feel upset": {"mental": -2, "social": -1}
            },
            "A sibling wants to swap toys.": {
                "Swap": {"social": 2},
                "Refuse": {"social": -1, "mental": 1}
            }
        }
    },

    "Teenage": {
        "choices": {
            "You have an important exam coming up.": {
                "Study": {"mental": 4, "wealth": -1},
                "Ignore it": {"mental": -3, "social": 2}
            },
            "Friends invite you to a party.": {
                "Go": {"social": 4, "mental": 1, "wealth": -2},
                "Stay home": {"mental": 2, "social": -2}
            },
            "You are offered a weekend job.": {
                "Take the job": {"wealth": 5, "mental": -2, "social": 1},
                "Decline": {"mental": 2, "wealth": -1}
            },
            "You're asked to try out for a sports team.": {
                "Try out": {"physical": 4, "social": 2, "mental": -1},
                "Skip it": {"physical": -1}
            },
            "You get into an argument with a friend.": {
                "Apologise": {"social": 2, "mental": 1},
                "Stay angry": {"social": -3, "mental": -2}
            }
        }
    },

    "Young Adult": {
        "choices": {
            "You receive an offer for further education.": {
                "Accept": {"mental": 4, "wealth": -3, "social": 2},
                "Decline": {"wealth": 2, "mental": -2}
            },
            "Your workplace offers overtime.": {
                "Accept": {"wealth": 5, "mental": -3, "social": -1},
                "Decline": {"mental": 2, "social": 1}
            },
            "Friends want to go on a short trip.": {
                "Go": {"social": 4, "wealth": -3, "mental": 2},
                "Stay home": {"wealth": 1, "social": -2}
            },
            "You're offered a chance to travel abroad.": {
                "Go": {"social": 3, "mental": 3, "wealth": -4},
                "Stay": {"wealth": 2}
            },
            "A relationship starts to get serious.": {
                "Commit": {"social": 4, "mental": 2},
                "Keep it casual": {"social": -1, "mental": 1}
            }
        }
    },

    "Adult": {
        "choices": {
            "You are considering changing careers.": {
                "Change career": {"mental": 4, "wealth": -3, "social": 1},
                "Stay where you are": {"wealth": 2, "mental": -1}
            },
            "You have saved enough for a major purchase.": {
                "Buy it": {"wealth": -4, "mental": 3},
                "Keep saving": {"wealth": 4, "mental": 1}
            },
            "You are invited to exercise with friends.": {
                "Join them": {"physical": 4, "social": 3},
                "Skip it": {"physical": -2, "social": -1}
            },
            "You're offered a leadership role at work.": {
                "Accept": {"wealth": 3, "mental": -2, "social": 1},
                "Decline": {"mental": 2}
            },
            "You have the chance to mentor someone younger.": {
                "Mentor them": {"social": 3, "mental": 2},
                "Focus on yourself": {"wealth": 1, "social": -1}
            }
        }
    },

    "Elderly": {
        "choices": {
            "A friend asks you to join a social group.": {
                "Join": {"social": 4, "mental": 3},
                "Stay home": {"social": -3, "mental": -1}
            },
            "You are encouraged to take up a gentle hobby.": {
                "Try it": {"mental": 4, "social": 2},
                "Decline": {"mental": -2}
            },
            "You have an opportunity to spend time with family.": {
                "Spend time together": {"social": 5, "mental": 2},
                "Stay alone": {"social": -3, "mental": -1}
            },
            "You're asked to share your life story with grandchildren.": {
                "Share it": {"social": 4, "mental": 3},
                "Keep it private": {"social": -2}
            },
            "You feel a bit under the weather.": {
                "See a doctor": {"physical": 2, "mental": 1},
                "Ignore it": {"physical": -3}
            }
        }
    }
}

# Rare wildcard events — bigger stat swings, roughly a 15% chance to trigger
# instead of a normal event, for a bit of unpredictability each playthrough.
special_events = {
    "Baby": {
        "You have a health scare and need urgent care.": {
            "Get help immediately": {"physical": 4, "mental": -2},
            "Wait and see": {"physical": -8, "mental": -3}
        }
    },
    "Childhood": {
        "You win a school talent show.": {
            "Celebrate": {"social": 5, "mental": 4},
            "Stay humble": {"social": 2, "mental": 2}
        }
    },
    "Teenage": {
        "You're caught up in a big rumour at school.": {
            "Confront it": {"social": -2, "mental": 2},
            "Ignore it": {"social": -5, "mental": -3}
        }
    },
    "Young Adult": {
        "You win a small amount of money unexpectedly.": {
            "Save it": {"wealth": 8, "mental": 1},
            "Spend it all": {"wealth": -2, "social": 3, "mental": 2}
        }
    },
    "Adult": {
        "You're involved in a minor car accident.": {
            "Handle it calmly": {"mental": -2, "wealth": -3},
            "Panic": {"mental": -5, "physical": -2}
        }
    },
    "Elderly": {
        "You're diagnosed with a manageable health condition.": {
            "Adapt your routine": {"physical": 2, "mental": 1},
            "Deny it's an issue": {"physical": -6, "mental": -2}
        }
    }
}