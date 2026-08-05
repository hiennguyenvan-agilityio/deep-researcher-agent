package deep_researcher.search

default allow := true

default search_platform := "duckduckgo"

search_platform := "exa" if input.user.id
