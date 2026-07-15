#!/usr/bin/env python3.11
"""
Wrap hardcoded English text in HTML templates with {% trans %}...{% endtrans %},
add missing msgid/msgstr entries to the Simplified Chinese PO file, and compile
the MO file.
"""
import re
import sys

CTFD = "/workspace/CTFd"
PO = CTFD + "/translations/zh_Hans_CN/LC_MESSAGES/messages.po"
MO = CTFD + "/translations/zh_Hans_CN/LC_MESSAGES/messages.mo"

# ---------------------------------------------------------------------------
# Replacements.
# Each entry: (filepath, kind, old_or_pattern, new)
#   kind "exact"  -> content.replace(old, new)  (replaces all occurrences)
#   kind "regex"  -> re.sub(pattern, new, content, flags=DOTALL)
# ---------------------------------------------------------------------------
REPLACEMENTS = []

def add(path, kind, old, new):
    REPLACEMENTS.append((path, kind, old, new))

# === FILE 1: admin/editor.html ===
p = CTFD + "/themes/admin/templates/editor.html"
add(p, "exact", "<h3>Content</h3>", "<h3>{% trans %}Content{% endtrans %}</h3>")
add(p, "exact", "<small class=\"text-muted\">This is the HTML content of your page</small>",
    "<small class=\"text-muted\">{% trans %}This is the HTML content of your page{% endtrans %}</small>")
add(p, "exact", 'data-toggle="tab">Write</a>', 'data-toggle="tab">{% trans %}Write{% endtrans %}</a>')
add(p, "exact", '<a class="nav-link preview-page" href="#">Preview</a>',
    '<a class="nav-link preview-page" href="#">{% trans %}Preview{% endtrans %}</a>')
add(p, "exact", "Media Library", "{% trans %}Media Library{% endtrans %}")
add(p, "exact", ">CTFd Page variables</a>", ">{% trans %}CTFd Page variables{% endtrans %}</a>")
add(p, "regex", r'(<button class="btn btn-primary" id="save-page">\s+)Save(\s+</button>)',
    r"\1{% trans %}Save{% endtrans %}\2")
add(p, "regex", r'(<h3 class="text-center py-3 d-block">\s+)Comments(\s+</h3>)',
    r"\1{% trans %}Comments{% endtrans %}\2")

# === FILE 2: admin/configs/backup.html ===
p = CTFD + "/themes/admin/templates/configs/backup.html"
add(p, "regex",
    r"<p>Exports are an archive of your CTF in its current state\. They can be re-imported into other CTFd\s+instances or used by scripts and third parties to calculate statistics\.</p>",
    "<p>{% trans %}Exports are an archive of your CTF in its current state. They can be re-imported into other CTFd instances or used by scripts and third parties to calculate statistics.{% endtrans %}</p>")
add(p, "exact", "<p>To download an export click the button below.</p>",
    "<p>{% trans %}To download an export click the button below.{% endtrans %}</p>")
add(p, "exact", 'class="btn btn-warning">Export</a>', 'class="btn btn-warning">{% trans %}Export{% endtrans %}</a>')
add(p, "regex",
    r"<p>You can import saved CTFd exports by uploading them below\. This will completely wipe your existing\s+CTFd instance and all your data will be replaced by the imported data\.\s+You should only import data that you trust!</p>",
    "<p>{% trans %}You can import saved CTFd exports by uploading them below. This will completely wipe your existing CTFd instance and all your data will be replaced by the imported data. You should only import data that you trust!{% endtrans %}</p>")
add(p, "exact", "Importing a CTFd export will completely wipe your existing data",
    "{% trans %}Importing a CTFd export will completely wipe your existing data{% endtrans %}")
add(p, "exact", '<label for="container-files">Import File</label>',
    '<label for="container-files">{% trans %}Import File{% endtrans %}</label>')
add(p, "exact", 'value="Import">', 'value="{% trans %}Import{% endtrans %}">')
add(p, "regex",
    r"CSVs exported from CTFd are not guaranteed to import back in via the Import CSV functionality\. See <a href=\"https://docs\.ctfd\.io/docs/imports/csv/\" target=\"_blank\">CSV Importing instructions</a> for details\.",
    '{% trans %}CSVs exported from CTFd are not guaranteed to import back in via the Import CSV functionality. See {% endtrans %}<a href="https://docs.ctfd.io/docs/imports/csv/" target="_blank">{% trans %}CSV Importing instructions{% endtrans %}</a>{% trans %} for details.{% endtrans %}')
add(p, "exact", 'value="Download CSV">', 'value="{% trans %}Download CSV{% endtrans %}">')
add(p, "exact", "Instructions and CSV templates", "{% trans %}Instructions and CSV templates{% endtrans %}")
add(p, "exact", 'value="Import CSV">', 'value="{% trans %}Import CSV{% endtrans %}">')

# === FILE 3: admin/configs/time.html ===
p = CTFD + "/themes/admin/templates/configs/time.html"
add(p, "regex",
    r"<p>This is the time when the competition will begin\. Challenges will automatically\s+unlock and users will be able to submit answers\.</p>",
    "<p>{% trans %}This is the time when the competition will begin. Challenges will automatically unlock and users will be able to submit answers.{% endtrans %}</p>")
add(p, "exact", "* All time fields required", "{% trans %}* All time fields required{% endtrans %}")
# Repeated labels (start/end/freeze) - replace all occurrences
add(p, "exact", ">Month:</label>", ">{% trans %}Month:{% endtrans %}</label>")
add(p, "exact", ">Day:</label>", ">{% trans %}Day:{% endtrans %}</label>")
add(p, "exact", ">Year:</label>", ">{% trans %}Year:{% endtrans %}</label>")
add(p, "exact", ">Hour:</label>", ">{% trans %}Hour:{% endtrans %}</label>")
add(p, "exact", ">Minute:</label>", ">{% trans %}Minute:{% endtrans %}</label>")
add(p, "exact", ">Timezone:</label>", ">{% trans %}Timezone:{% endtrans %}</label>")
add(p, "exact", ">Local Time:</label>", ">{% trans %}Local Time:{% endtrans %}</label>")
add(p, "exact", ">Timezone Time:</label>", ">{% trans %}Timezone Time:{% endtrans %}</label>")
add(p, "exact", ">UTC Timestamp:</label>", ">{% trans %}UTC Timestamp:{% endtrans %}</label>")
add(p, "regex",
    r"<p>This is the time when the competition will end\. Challenges will automatically\s+close and users won't be able to submit answers\.</p>",
    "<p>{% trans %}This is the time when the competition will end. Challenges will automatically close and users won't be able to submit answers.{% endtrans %}</p>")
add(p, "exact",
    "Allows challenges to be viewed after the End Time, however no new submissions will be recorded.<br>",
    "{% trans %}Allows challenges to be viewed after the End Time, however no new submissions will be recorded.{% endtrans %}<br>")
add(p, "exact",
    "For participants to be able to submit after End Time but not alter the scoreboard, configure Freeze Time to be your End Time.",
    "{% trans %}For participants to be able to submit after End Time but not alter the scoreboard, configure Freeze Time to be your End Time.{% endtrans %}")
add(p, "regex",
    r"<p>Freeze time specifies the timestamp that the competition will be frozen to\.\s+All solves before the freeze time will be shown, but new solves won't be shown to\s+users\. </p>",
    "<p>{% trans %}Freeze time specifies the timestamp that the competition will be frozen to. All solves before the freeze time will be shown, but new solves won't be shown to users.{% endtrans %}</p>")
add(p, "exact", ">CTF Timezone:</label>", ">{% trans %}CTF Timezone:{% endtrans %}</label>")
add(p, "exact", ">Update</button>", ">{% trans %}Update{% endtrans %}</button>")

# === FILE 4: admin/configs/robots.html ===
p = CTFD + "/themes/admin/templates/configs/robots.html"
add(p, "exact",
    "The <code>robots.txt</code> file contains instructions that suggest to bots which webpages they should and should not access. Not all bots respect <code>robots.txt</code>.",
    "{% trans %}The <code>robots.txt</code> file contains instructions that suggest to bots which webpages they should and should not access. Not all bots respect <code>robots.txt</code>.{% endtrans %}")
add(p, "exact", ">Update</button>", ">{% trans %}Update{% endtrans %}</button>")

# === FILE 5: admin/configs/sanitize.html ===
p = CTFD + "/themes/admin/templates/configs/sanitize.html"
add(p, "exact", "Whether CTFd will attempt to sanitize HTML content from content.",
    "{% trans %}Whether CTFd will attempt to sanitize HTML content from content.{% endtrans %}")
add(p, "exact", "Required (Disable in config.ini)", "{% trans %}Required (Disable in config.ini){% endtrans %}")
add(p, "exact", "Enabled", "{% trans %}Enabled{% endtrans %}")
add(p, "exact", "Disabled", "{% trans %}Disabled{% endtrans %}")
add(p, "exact", ">Update</button>", ">{% trans %}Update{% endtrans %}</button>")

# === FILE 6: admin/configs/usermode.html ===
p = CTFD + "/themes/admin/templates/configs/usermode.html"
add(p, "exact",
    "Controls whether users play as themselves ({% trans %}User Mode{% endtrans %}) or join together as teams (Team Mode).",
    "Controls whether users play as themselves ({% trans %}User Mode{% endtrans %}) or join together as teams ({% trans %}Team Mode{% endtrans %}).")
add(p, "exact", "<li>Participants register accounts and form teams</li>",
    "<li>{% trans %}Participants register accounts and form teams{% endtrans %}</li>")
add(p, "exact", "<li>If a team member solves a challenge, the entire team receives credit</li>",
    "<li>{% trans %}If a team member solves a challenge, the entire team receives credit{% endtrans %}</li>")
add(p, "exact", "<li>Easier to see which team member solved a challenge</li>",
    "<li>{% trans %}Easier to see which team member solved a challenge{% endtrans %}</li>")
add(p, "exact", "<li>May be slightly more difficult to administer</li>",
    "<li>{% trans %}May be slightly more difficult to administer{% endtrans %}</li>")
add(p, "exact", "<li>Participants only register an individual account</li>",
    "<li>{% trans %}Participants only register an individual account{% endtrans %}</li>")
add(p, "exact", "<li>Players can share accounts to form pseudo-teams</li>",
    "<li>{% trans %}Players can share accounts to form pseudo-teams{% endtrans %}</li>")
add(p, "exact", "<li>Easier to organize</li>",
    "<li>{% trans %}Easier to organize{% endtrans %}</li>")
add(p, "exact", "<li>Difficult to attribute solutions to individual team members</li>",
    "<li>{% trans %}Difficult to attribute solutions to individual team members{% endtrans %}</li>")
add(p, "exact",
    "<strong>Changing your user mode will also delete all submissions or records that a user took an action.</strong>",
    "<strong>{% trans %}Changing your user mode will also delete all submissions or records that a user took an action.{% endtrans %}</strong>")
add(p, "exact", "<small>(Submissions, Awards, Unlocks, Tracking)</small>",
    "<small>{% trans %}(Submissions, Awards, Unlocks, Tracking){% endtrans %}</small>")
add(p, "exact", "Update", "{% trans %}Update{% endtrans %}")

# === FILE 7: admin/users/user.html ===
p = CTFD + "/themes/admin/templates/users/user.html"
add(p, "exact", '<span class="badge badge-primary">admin</span>',
    '<span class="badge badge-primary">{% trans %}admin{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-success">verified</span>',
    '<span class="badge badge-success">{% trans %}verified{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-danger">hidden</span>',
    '<span class="badge badge-danger">{% trans %}hidden{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-danger">banned</span>',
    '<span class="badge badge-danger">{% trans %}banned{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-primary">Official</span>',
    '<span class="badge badge-primary">{% trans %}Official{% endtrans %}</span>')
add(p, "exact", "<small>place</small>", "<small>{% trans %}place{% endtrans %}</small>")
add(p, "exact", "<small>points</small>", "<small>{% trans %}points{% endtrans %}</small>")
add(p, "exact", '<h3 class="text-center pt-5 d-block">Solves</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Solves{% endtrans %}</h3>')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Fails</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Fails{% endtrans %}</h3>')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Awards</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Awards{% endtrans %}</h3>')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Missing</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Missing{% endtrans %}</h3>')
# table headers - replace all occurrences
add(p, "exact", "<b>Challenge</b>", "<b>{% trans %}Challenge{% endtrans %}</b>")
add(p, "exact", "<b>Submitted</b>", "<b>{% trans %}Submitted{% endtrans %}</b>")
add(p, "exact", "<b>Category</b>", "<b>{% trans %}Category{% endtrans %}</b>")
add(p, "exact", "<b>Value</b>", "<b>{% trans %}Value{% endtrans %}</b>")
add(p, "exact", "<b>Time</b>", "<b>{% trans %}Time{% endtrans %}</b>")
add(p, "exact", "<b>Name</b>", "<b>{% trans %}Name{% endtrans %}</b>")
add(p, "exact", "<b>Description</b>", "<b>{% trans %}Description{% endtrans %}</b>")
add(p, "exact", "<b>Date</b>", "<b>{% trans %}Date{% endtrans %}</b>")
add(p, "exact", "<b>Icon</b>", "<b>{% trans %}Icon{% endtrans %}</b>")

# === FILE 8: admin/teams/team.html ===
p = CTFD + "/themes/admin/templates/teams/team.html"
add(p, "exact", "Share this link for users to join this team",
    "{% trans %}Share this link for users to join this team{% endtrans %}")
add(p, "exact", '<label for="award-member-input">Member</label>',
    '<label for="award-member-input">{% trans %}Member{% endtrans %}</label>')
add(p, "exact", '<span class="badge badge-success">verified</span>',
    '<span class="badge badge-success">{% trans %}verified{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-danger">hidden</span>',
    '<span class="badge badge-danger">{% trans %}hidden{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-danger">banned</span>',
    '<span class="badge badge-danger">{% trans %}banned{% endtrans %}</span>')
add(p, "exact", '<span class="badge badge-primary">Official</span>',
    '<span class="badge badge-primary">{% trans %}Official{% endtrans %}</span>')
add(p, "exact", '<h2 class="text-center">{{ members | length }} members</h2>',
    '<h2 class="text-center">{% trans count=members|length %}{{ count }} members{% endtrans %}</h2>')
add(p, "exact", "<small>place</small>", "<small>{% trans %}place{% endtrans %}</small>")
add(p, "exact", "<small>points</small>", "<small>{% trans %}points{% endtrans %}</small>")
add(p, "exact", '<h3 class="text-center">Team Members</h3>',
    '<h3 class="text-center">{% trans %}Team Members{% endtrans %}</h3>')
add(p, "exact", "<b>User Name</b>", "<b>{% trans %}User Name{% endtrans %}</b>")
add(p, "exact", "<b>E-Mail</b>", "<b>{% trans %}E-Mail{% endtrans %}</b>")
add(p, "exact", "<b>Score</b>", "<b>{% trans %}Score{% endtrans %}</b>")
add(p, "exact", '<span class="badge badge-primary">Captain</span>',
    '<span class="badge badge-primary">{% trans %}Captain{% endtrans %}</span>')
add(p, "exact", 'title="Remove {{ member.name }}"',
    'title="{% trans name=member.name %}Remove {{ name }}{% endtrans %}"')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Solves</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Solves{% endtrans %}</h3>')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Fails</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Fails{% endtrans %}</h3>')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Awards</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Awards{% endtrans %}</h3>')
add(p, "exact", '<h3 class="text-center pt-5 d-block">Missing</h3>',
    '<h3 class="text-center pt-5 d-block">{% trans %}Missing{% endtrans %}</h3>')
add(p, "exact", "<b>Challenge</b>", "<b>{% trans %}Challenge{% endtrans %}</b>")
add(p, "exact", "<b>User</b>", "<b>{% trans %}User{% endtrans %}</b>")
add(p, "exact", "<b>Submitted</b>", "<b>{% trans %}Submitted{% endtrans %}</b>")
add(p, "exact", "<b>Category</b>", "<b>{% trans %}Category{% endtrans %}</b>")
add(p, "exact", "<b>Value</b>", "<b>{% trans %}Value{% endtrans %}</b>")
add(p, "exact", "<b>Time</b>", "<b>{% trans %}Time{% endtrans %}</b>")
add(p, "exact", "<b>Name</b>", "<b>{% trans %}Name{% endtrans %}</b>")
add(p, "exact", "<b>Description</b>", "<b>{% trans %}Description{% endtrans %}</b>")
add(p, "exact", "<b>Date</b>", "<b>{% trans %}Date{% endtrans %}</b>")
add(p, "exact", "<b>Icon</b>", "<b>{% trans %}Icon{% endtrans %}</b>")

# === FILE 9: admin/modals/users/addresses.html ===
p = CTFD + "/themes/admin/templates/modals/users/addresses.html"
add(p, "exact", "<b>IP Address</b>", "<b>{% trans %}IP Address{% endtrans %}</b>")
add(p, "exact", "<b>Last Seen</b>", "<b>{% trans %}Last Seen{% endtrans %}</b>")
add(p, "exact", "<b>City</b>", "<b>{% trans %}City{% endtrans %}</b>")
add(p, "exact", "<b>Country</b>", "<b>{% trans %}Country{% endtrans %}</b>")
add(p, "exact", ">IP Geolocation by DB-IP</a>", ">{% trans %}IP Geolocation by DB-IP{% endtrans %}</a>")

# === FILE 10: admin/challenges/update.html ===
p = CTFD + "/themes/admin/templates/challenges/update.html"
add(p, "exact", "Name<br>", "{% trans %}Name{% endtrans %}<br>")
add(p, "exact", "Challenge Name", "{% trans %}Challenge Name{% endtrans %}")
add(p, "exact", "Category<br>", "{% trans %}Category{% endtrans %}<br>")
add(p, "exact", "Challenge Category", "{% trans %}Challenge Category{% endtrans %}")
add(p, "exact", "Message<br>", "{% trans %}Message{% endtrans %}<br>")
add(p, "exact", "Use this to give a brief introduction to your challenge.",
    "{% trans %}Use this to give a brief introduction to your challenge.{% endtrans %}")
add(p, "exact", "Attribution:<br>", "{% trans %}Attribution:{% endtrans %}<br>")
add(p, "exact", "Attribution for your challenge <small>(supports markdown)</small>",
    "{% trans %}Attribution for your challenge{% endtrans %} <small>{% trans %}(supports markdown){% endtrans %}</small>")
add(p, "exact", "Connection Info<br>", "{% trans %}Connection Info{% endtrans %}<br>")
add(p, "exact", "Use this to specify a link, hostname, or connection instructions for your challenge.",
    "{% trans %}Use this to specify a link, hostname, or connection instructions for your challenge.{% endtrans %}")
add(p, "exact", "This is how many points teams will receive once they solve this challenge.",
    "{% trans %}This is how many points teams will receive once they solve this challenge.{% endtrans %}")
add(p, "exact", "Position<br>", "{% trans %}Position{% endtrans %}<br>")
add(p, "exact", "This is used to order the challenge. Lower positions are first. Position 0 goes to the end to be sorted by challenge value.",
    "{% trans %}This is used to order the challenge. Lower positions are first. Position 0 goes to the end to be sorted by challenge value.{% endtrans %}")
add(p, "exact", "Scoring Function<br>", "{% trans %}Scoring Function{% endtrans %}<br>")
add(p, "exact", "<span>How the challenge value will be calculated based on the Decay value</span>",
    "<span>{% trans %}How the challenge value will be calculated based on the Decay value{% endtrans %}</span>")
add(p, "exact", ">Static</option>", ">{% trans %}Static{% endtrans %}</option>")
add(p, "exact", ">Linear</option>", ">{% trans %}Linear{% endtrans %}</option>")
add(p, "exact", ">Logarithmic</option>", ">{% trans %}Logarithmic{% endtrans %}</option>")
add(p, "exact", "<li>Static: Challenge <code>Value</code> is awarded as-is</li>",
    "<li>{% trans %}Static: Challenge <code>Value</code> is awarded as-is{% endtrans %}</li>")
add(p, "exact", "<li>Linear: Calculated as <code>Initial - (Decay * SolveCount)</code></li>",
    "<li>{% trans %}Linear: Calculated as <code>Initial - (Decay * SolveCount)</code>{% endtrans %}</li>")
add(p, "exact", "<li>Logarithmic: Calculated as <code>(((Minimum - Initial) / (Decay^2)) * (SolveCount^2)) + Initial</code></li>",
    "<li>{% trans %}Logarithmic: Calculated as <code>(((Minimum - Initial) / (Decay^2)) * (SolveCount^2)) + Initial</code>{% endtrans %}</li>")
add(p, "exact", "Initial Value<br>", "{% trans %}Initial Value{% endtrans %}<br>")
add(p, "exact", "This is how many points the challenge was worth initially.",
    "{% trans %}This is how many points the challenge was worth initially.{% endtrans %}")
add(p, "exact", "Decay<br>", "{% trans %}Decay{% endtrans %}<br>")
add(p, "exact", "<span>The decay value is used differently depending on the above Decay Function</span>",
    "<span>{% trans %}The decay value is used differently depending on the above Decay Function{% endtrans %}</span>")
add(p, "exact", "<li>Linear: The amount of points deducted per solve. Equal deduction per solve.</li>",
    "<li>{% trans %}Linear: The amount of points deducted per solve. Equal deduction per solve.{% endtrans %}</li>")
add(p, "exact", "<li>Logarithmic: The amount of solves before the challenge reaches its minimum value. Earlier solves will lose less points. Later solves will lose more points</li>",
    "<li>{% trans %}Logarithmic: The amount of solves before the challenge reaches its minimum value. Earlier solves will lose less points. Later solves will lose more points{% endtrans %}</li>")
add(p, "exact", "Minimum Value<br>", "{% trans %}Minimum Value{% endtrans %}<br>")
add(p, "exact", "Value<br>", "{% trans %}Value{% endtrans %}<br>")
add(p, "exact", "This is the lowest that the challenge can be worth",
    "{% trans %}This is the lowest that the challenge can be worth{% endtrans %}")
add(p, "exact", "Logic<br>", "{% trans %}Logic{% endtrans %}<br>")
add(p, "exact", "<small class=\"form-text text-muted\">Determines how this challenge is solved</small>",
    "<small class=\"form-text text-muted\">{% trans %}Determines how this challenge is solved{% endtrans %}</small>")
add(p, "exact", ">Require Any Flag</option>", ">{% trans %}Require Any Flag{% endtrans %}</option>")
add(p, "exact", ">Require All Flags</option>", ">{% trans %}Require All Flags{% endtrans %}</option>")
add(p, "exact", ">Require Any Flags by All Team Members</option>", ">{% trans %}Require Any Flags by All Team Members{% endtrans %}</option>")
add(p, "exact", "Max Attempts<br>", "{% trans %}Max Attempts{% endtrans %}<br>")
add(p, "exact", "Maximum amount of attempts users receive. Leave at 0 for unlimited.",
    "{% trans %}Maximum amount of attempts users receive. Leave at 0 for unlimited.{% endtrans %}")
add(p, "exact", "State<br>", "{% trans %}State{% endtrans %}<br>")
add(p, "exact", "<small class=\"form-text text-muted\">Changes the state of the challenge (e.g. visible, hidden)</small>",
    "<small class=\"form-text text-muted\">{% trans %}Changes the state of the challenge (e.g. visible, hidden){% endtrans %}</small>")
add(p, "exact", ">Visible</option>", ">{% trans %}Visible{% endtrans %}</option>")
add(p, "exact", ">Hidden</option>", ">{% trans %}Hidden{% endtrans %}</option>")
add(p, "exact", "Update", "{% trans %}Update{% endtrans %}")

# === FILE 11: core/config.html ===
p = CTFD + "/themes/core/templates/config.html"
add(p, "exact", "<label>Challenge Window Size</label>",
    "<label>{% trans %}Challenge Window Size{% endtrans %}</label>")
add(p, "exact", ">Small</option>", ">{% trans %}Small{% endtrans %}</option>")
add(p, "exact", ">Normal</option>", ">{% trans %}Normal{% endtrans %}</option>")
add(p, "exact", ">Large</option>", ">{% trans %}Large{% endtrans %}</option>")
add(p, "exact", ">Extra Large</option>", ">{% trans %}Extra Large{% endtrans %}</option>")
add(p, "exact", "Challenge Category Order Custom Function<br>",
    "{% trans %}Challenge Category Order Custom Function{% endtrans %}<br>")
add(p, "exact", "Challenge Order Custom Function<br>",
    "{% trans %}Challenge Order Custom Function{% endtrans %}<br>")
add(p, "exact", "Define a ", "{% trans %}Define a {% endtrans %}")
add(p, "exact", ">custom compareFn function for Array.sort()</a>",
    ">{% trans %}custom compareFn function for Array.sort(){% endtrans %}</a>")
add(p, "regex", r"</a>\s+used to sort the challenge categories",
    "</a>{% trans %} used to sort the challenge categories{% endtrans %}")
add(p, "regex", r"</a>\s+used to sort the challenges within categories",
    "</a>{% trans %} used to sort the challenges within categories{% endtrans %}")
add(p, "exact", "Use Built-In Syntax Highlighter", "{% trans %}Use Built-In Syntax Highlighter{% endtrans %}")
add(p, "exact",
    "The built-in syntax highlighter is lightweight and fast but may not always correctly highlight all languages. You can disable the built-in highlighter in order to use your own.",
    "{% trans %}The built-in syntax highlighter is lightweight and fast but may not always correctly highlight all languages. You can disable the built-in highlighter in order to use your own.{% endtrans %}")
add(p, "exact", ">Update</button>", ">{% trans %}Update{% endtrans %}</button>")

# === FILE 12: core-deprecated/errors/404.html ===
p = CTFD + "/themes/core-deprecated/templates/errors/404.html"
add(p, "exact", "<h2>File not found</h2>", "<h2>{% trans %}File not found{% endtrans %}</h2>")
add(p, "exact", "<h2>Sorry about that</h2>", "<h2>{% trans %}Sorry about that{% endtrans %}</h2>")

# === FILE 13: core-deprecated/errors/401.html ===
p = CTFD + "/themes/core-deprecated/templates/errors/401.html"
add(p, "exact", "<h1>Unauthorized</h1>", "<h1>{% trans %}Unauthorized{% endtrans %}</h1>")

# === FILE 14: core-deprecated/errors/429.html ===
p = CTFD + "/themes/core-deprecated/templates/errors/429.html"
add(p, "exact", "<h2>Too many requests</h2>", "<h2>{% trans %}Too many requests{% endtrans %}</h2>")
add(p, "exact", "<h2>Please slow down!</h2>", "<h2>{% trans %}Please slow down!{% endtrans %}</h2>")

# === FILE 15: core-deprecated/errors/403.html ===
p = CTFD + "/themes/core-deprecated/templates/errors/403.html"
add(p, "exact", "<h1>Forbidden</h1>", "<h1>{% trans %}Forbidden{% endtrans %}</h1>")


# ---------------------------------------------------------------------------
# msgid -> Simplified Chinese translation (only missing ones get appended).
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    # editor.html
    "Write": "编写",
    "Preview": "预览",
    "Media Library": "媒体库",
    "CTFd Page variables": "CTFd 页面变量",
    # backup.html
    "Exports are an archive of your CTF in its current state. They can be re-imported into other CTFd instances or used by scripts and third parties to calculate statistics.":
        "导出文件是 CTF 当前状态的归档。它们可以重新导入到其他 CTFd 实例中，或被脚本和第三方用于计算统计数据。",
    "To download an export click the button below.": "点击下方按钮以下载导出文件。",
    "You can import saved CTFd exports by uploading them below. This will completely wipe your existing CTFd instance and all your data will be replaced by the imported data. You should only import data that you trust!":
        "你可以通过在下方上传已保存的 CTFd 导出文件来进行导入。这将完全清除你现有的 CTFd 实例，所有数据都将被导入的数据替换。请仅导入你信任的数据！",
    "Importing a CTFd export will completely wipe your existing data": "导入 CTFd 导出文件将完全清除你现有的数据",
    "CSVs exported from CTFd are not guaranteed to import back in via the Import CSV functionality. See ":
        "从 CTFd 导出的 CSV 不保证能够通过导入 CSV 功能重新导入。详见 ",
    " for details.": "了解详情。",
    "Instructions and CSV templates": "说明和 CSV 模板",
    # time.html
    "This is the time when the competition will begin. Challenges will automatically unlock and users will be able to submit answers.":
        "这是比赛开始的时间。题目将自动解锁，用户将可以提交答案。",
    "* All time fields required": "* 所有时间字段均为必填",
    "Month:": "月：",
    "Day:": "日：",
    "Year:": "年：",
    "Hour:": "时：",
    "Minute:": "分：",
    "Timezone:": "时区：",
    "Local Time:": "本地时间：",
    "Timezone Time:": "时区时间：",
    "UTC Timestamp:": "UTC 时间戳：",
    "This is the time when the competition will end. Challenges will automatically close and users won't be able to submit answers.":
        "这是比赛结束的时间。题目将自动关闭，用户将无法提交答案。",
    "Allows challenges to be viewed after the End Time, however no new submissions will be recorded.":
        "允许在结束时间之后查看题目，但不会记录新的提交。",
    "For participants to be able to submit after End Time but not alter the scoreboard, configure Freeze Time to be your End Time.":
        "若要让参赛者在结束时间之后仍能提交但不影响记分板，请将冻结时间设置为你的结束时间。",
    "Freeze time specifies the timestamp that the competition will be frozen to. All solves before the freeze time will be shown, but new solves won't be shown to users.":
        "冻结时间指定比赛将冻结到的时间戳。冻结时间之前的所有解答将会显示，但新的解答不会显示给用户。",
    "CTF Timezone:": "CTF 时区：",
    # robots.html
    "The <code>robots.txt</code> file contains instructions that suggest to bots which webpages they should and should not access. Not all bots respect <code>robots.txt</code>.":
        "<code>robots.txt</code> 文件包含向机器人建议其应访问和不应访问哪些网页的指令。并非所有机器人都遵守 <code>robots.txt</code>。",
    # sanitize.html
    "Whether CTFd will attempt to sanitize HTML content from content.":
        "CTFd 是否尝试对内容中的 HTML 内容进行净化处理。",
    "Required (Disable in config.ini)": "必需（在 config.ini 中禁用）",
    # usermode.html
    "Participants register accounts and form teams": "参赛者注册账号并组建队伍",
    "If a team member solves a challenge, the entire team receives credit": "如果队员解出一道题，整个队伍都会获得积分",
    "Easier to see which team member solved a challenge": "更容易查看是哪位队员解出了题目",
    "May be slightly more difficult to administer": "管理上可能稍微困难一些",
    "Participants only register an individual account": "参赛者仅注册个人账号",
    "Players can share accounts to form pseudo-teams": "玩家可以共享账号以组建伪队伍",
    "Changing your user mode will also delete all submissions or records that a user took an action.":
        "更改用户模式还会删除用户采取操作的所有提交或记录。",
    "(Submissions, Awards, Unlocks, Tracking)": "（提交、奖励、解锁、跟踪）",
    # team.html
    "Share this link for users to join this team": "分享此链接供用户加入该队伍",
    "%(count)s members": "%(count)s 名成员",
    "Remove %(name)s": "移除 %(name)s",
    # addresses.html
    "IP Geolocation by DB-IP": "由 DB-IP 提供 IP 地理定位",
    # challenges/update.html
    "Message": "消息",
    "Use this to give a brief introduction to your challenge.": "用于为你的题目提供简要介绍。",
    "Attribution:": "署名：",
    "Attribution for your challenge": "你的题目的署名",
    "(supports markdown)": "（支持 markdown）",
    "Connection Info": "连接信息",
    "Use this to specify a link, hostname, or connection instructions for your challenge.":
        "用于为你的题目指定链接、主机名或连接说明。",
    "This is how many points teams will receive once they solve this challenge.":
        "这是队伍解出该题目后将获得的分数。",
    "Position": "位置",
    "This is used to order the challenge. Lower positions are first. Position 0 goes to the end to be sorted by challenge value.":
        "用于对题目进行排序。位置越靠前越优先。位置 0 会排到末尾，并按题目分值排序。",
    "Scoring Function": "计分函数",
    "Static: Challenge <code>Value</code> is awarded as-is": "静态：按题目 <code>分值</code> 原样奖励",
    "Linear: Calculated as <code>Initial - (Decay * SolveCount)</code>":
        "线性：计算方式为 <code>初始值 - (衰减 * 解题数)</code>",
    "Logarithmic: Calculated as <code>(((Minimum - Initial) / (Decay^2)) * (SolveCount^2)) + Initial</code>":
        "对数：计算方式为 <code>(((最小值 - 初始值) / (衰减^2)) * (解题数^2)) + 初始值</code>",
    "This is how many points the challenge was worth initially.": "这是题目最初的分值。",
    "Decay": "衰减",
    "Linear: The amount of points deducted per solve. Equal deduction per solve.":
        "线性：每次解题扣除的分数。每次解题扣除相同的分数。",
    "Logarithmic: The amount of solves before the challenge reaches its minimum value. Earlier solves will lose less points. Later solves will lose more points":
        "对数：题目达到最低分值前的解题次数。较早的解题损失较少分数，较晚的解题损失较多分数",
    "This is the lowest that the challenge can be worth": "这是题目可以拥有的最低分值",
    "Logic": "逻辑",
    "Max Attempts": "最大尝试次数",
    "Maximum amount of attempts users receive. Leave at 0 for unlimited.":
        "用户获得的最大尝试次数。设为 0 表示不限次数。",
    # config.html
    "Challenge Category Order Custom Function": "题目分类排序自定义函数",
    "custom compareFn function for Array.sort()": "用于 Array.sort() 的自定义 compareFn 函数",
    " used to sort the challenge categories": " 用于对题目分类进行排序",
    "Challenge Order Custom Function": "题目排序自定义函数",
    " used to sort the challenges within categories": " 用于对分类内的题目进行排序",
    "Define a ": "定义一个 ",
    "Use Built-In Syntax Highlighter": "使用内置语法高亮",
    "The built-in syntax highlighter is lightweight and fast but may not always correctly highlight all languages. You can disable the built-in highlighter in order to use your own.":
        "内置语法高亮器轻量且快速，但可能无法始终正确高亮所有语言。你可以禁用内置高亮器以使用自己的高亮器。",
    # error pages
    "Unauthorized": "未授权",
    "Forbidden": "禁止访问",
}


def po_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def main():
    errors = []

    # 1) Apply HTML replacements.
    files_touched = set()
    for path, kind, old, new in REPLACEMENTS:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        original = content
        if kind == "exact":
            if old not in content:
                errors.append("NOT FOUND (exact) in %s: %r" % (path, old[:80]))
                continue
            content = content.replace(old, new)
        elif kind == "regex":
            pattern = re.compile(old, re.DOTALL)
            if not pattern.search(content):
                errors.append("NOT FOUND (regex) in %s: %r" % (path, old[:80]))
                continue
            content = pattern.sub(new, content)
        if content == original:
            errors.append("NO CHANGE in %s: %r" % (path, old[:80]))
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        files_touched.add(path)

    if errors:
        print("=== REPLACEMENT ERRORS ===")
        for e in errors:
            print(" -", e)
        print("Aborting before PO update due to replacement errors.")
        sys.exit(1)

    print("Applied replacements to %d files." % len(files_touched))

    # 2) Read existing PO msgids.
    from babel.messages.pofile import read_po
    with open(PO, "rb") as f:
        catalog = read_po(f)
    existing = set()
    for m in catalog:
        if m.id:
            existing.add(m.id[0] if isinstance(m.id, tuple) else m.id)
    print("Existing PO entries: %d" % len(existing))

    # 3) Append missing entries.
    to_add = [(k, TRANSLATIONS[k]) for k in TRANSLATIONS if k not in existing]
    print("New entries to add: %d" % len(to_add))

    if to_add:
        with open(PO, "ab") as f:
            for msgid, msgstr in to_add:
                block = '\nmsgid "%s"\nmsgstr "%s"\n' % (po_escape(msgid), po_escape(msgstr))
                f.write(block.encode("utf-8"))
        print("Appended %d new entries to PO." % len(to_add))
    else:
        print("No new entries needed.")

    # 4) Compile MO.
    from babel.messages.mofile import write_mo
    with open(PO, "rb") as f:
        catalog = read_po(f)
    with open(MO, "wb") as f:
        write_mo(f, catalog)
    print("Compiled MO file: %s" % MO)

    # 5) Summary of added entries.
    print("\n=== ADDED ENTRIES ===")
    for msgid, msgstr in to_add:
        print(" * %s -> %s" % (msgid, msgstr))


if __name__ == "__main__":
    main()
