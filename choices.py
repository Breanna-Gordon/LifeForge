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
            }
        }
    }
}
