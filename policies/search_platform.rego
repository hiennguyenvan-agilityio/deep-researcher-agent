package deep_researcher.search_platform

default search_tool := "duckduckgo"

search_tool := "exa" if input.user.id
