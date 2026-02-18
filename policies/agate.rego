package agate

default allow := false

# baseline role->tool allow-list
role_tools := {
  "support_agent": {"read_ticket", "send_email", "query_logs"},
  "devops_agent": {"read_ticket", "query_logs", "run_shell", "send_email"}
}

allow if {
  role_tools[input.role][input.tool]
  valid_args
}

valid_args if {
  input.tool == "send_email"
  endswith(lower(input.args.recipient), "@company.com")
}

valid_args if {
  input.tool == "run_shell"
  not contains(lower(input.args.command), "curl")
  not contains(lower(input.args.command), "wget")
  not contains(lower(input.args.command), "nc ")
}

valid_args if {
  input.tool == "query_logs"
}

valid_args if {
  input.tool == "read_ticket"
}
