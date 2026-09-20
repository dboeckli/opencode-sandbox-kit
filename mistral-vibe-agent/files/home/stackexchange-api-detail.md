# Stack Exchange API Reference (Detail)

- **API-Version (`api_revision`)**: `2026.5.26.43284`
- **Abfragedatum**: 2026-08-11 (Quelle: `GET /2.3/info?site=stackoverflow` → `items[0].api_revision`; ohne Auth abrufbar)
- **Basis-URL**: `https://api.stackexchange.com/2.3`
- **Auth**: `Authorization: Bearer $STACKOVERFLOW_API_KEY` (Platzhalter `proxy-managed` in der Sandbox)
- **Pflicht-Parameter**: `site` (z. B. `stackoverflow`) bei fast allen Methoden; Methoden-Pflichtparameter stehen im Text.
- **Kompakte Version**: `~/stackexchange-api.md` (eine Tabelle) — diese Detail-Version nur bei Bedarf lesen
- **Offizielle Doku**: https://api.stackexchange.com/docs (nur bei Unklarheiten abrufen)

## Generische Parameter

Fast alle Methoden akzeptieren diese Parameter (nur `page`/`pagesize`/`site` sind universell):

| Parameter | Typ | Beschreibung |
|---|---|---|
| `site` | string | Stack Exchange-Site, z. B. `stackoverflow` (bei den meisten Methoden Pflicht) |
| `page` | number | 1-basierte Seitennummer (Default 1) |
| `pagesize` | number | Einträge pro Seite, 1–100 (Default 30) |
| `fromdate` | date | Unix-Timestamp; nur Ergebnisse ab diesem Datum |
| `todate` | date | Unix-Timestamp; nur Ergebnisse bis zu diesem Datum |
| `order` | `desc`\|`asc` | Sortierrichtung (Default `desc`) |
| `min` | depends | Untergrenze für den `sort`-Wert |
| `max` | depends | Obergrenze für den `sort`-Wert |
| `sort` | string | Sortierfeld, methodenspezifisch (siehe Methode) |
| `filter` | string | Custom/Default-Filter (z. B. `!nNPvSNdWme`) |
| `key` | key | API-Key (bei Antworten ohne Key gekürzt; hier via Proxy-Header) |
| `access_token` | access_token | OAuth-Token für authentifizierte Methoden |
| `preview` | `true`\|`false` | Write-Methoden: simuliert die Aktion ohne Ausführung |

## Antwort-Wrapper

Jede Antwort ist ein JSON-Objekt: `{"items": [...], "has_more": bool, "quota_max": n, "quota_remaining": n}`. 
`items` enthält die Daten, `has_more` ob weitere Seiten existieren (`page` erhöhen bis `has_more == false`).


## GET-Methoden (142)

### `GET /users/{id}/achievements` (access_token)

Returns a user's recent network-wide achievements, given their account id.

Methodenspezifische Parameter: `scope: "private_info", id: "number"`

### `GET /search/advanced`

Searches a site for any questions which fit the given criteria.

Methodenspezifische Parameter: `q: "string", accepted: ["", "True", "False"], answers: "number", body: "string", closed: ["", "True", "False"], migrated: ["", "True", "False"], notice: ["", "True", "False"], nottagged: "string list", tagged: "string list", title: "string", user: "number", url: "string", views: "number", wiki: ["", "True", "False"]`
; sort: activity, votes, creation, relevance

### `GET /answers/{id}/flags/options` (access_token)

Returns the different flags that the user identified with an access_token can create for the answer identified by {id}. Available flags vary from post to post and user to user, an app should never assume a particular flag can be created without consulting this method.

Methodenspezifische Parameter: `id: "number"`

### `GET /collectives/{slugs}/answers`

Returns answer objects belonging to Collectives in {slugs} found on the site.

Methodenspezifische Parameter: `slugs: "string list"`
; sort: activity, creation, votes

### `GET /answers/{ids}`

Gets the set of answers identified by ids.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, creation, votes

### `GET /questions/{ids}/answers`

Gets the answers to a set of questions identified in id.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, creation, votes

### `GET /users/{ids}/answers`

Returns the answers the users in {ids} have posted.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, creation, votes

### `GET /answers`

Returns all the undeleted answers in the system.
; sort: activity, creation, votes

### `GET /apps/{accessTokens}/de-authenticate`

Passing valid access_tokens to this method causes the application that created them to be de-authorized by the user associated with each access_token . This will remove the application from their apps tab, and cause all other existing access_tokens to be destroyed.

Methodenspezifische Parameter: `accessTokens: "string list"`

### `GET /users/{ids}/associated`

Returns all of a user's associated accounts, given their account_ids in {ids}.

Methodenspezifische Parameter: `ids: "number list", types: "string"`

### `GET /badges/{ids}/recipients`

Returns recently awarded badges in the system, constrained to a certain set of badges.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /badges/recipients`

Returns recently awarded badges in the system.

### `GET /badges/{ids}`

Gets the badges identified in id.

Methodenspezifische Parameter: `ids: "number list"`
; sort: rank, name, type

### `GET /badges/name`

Gets all explicitly named badges in the system.

Methodenspezifische Parameter: `inname: "string"`
; sort: rank, name

### `GET /badges/tags`

Returns the badges that are awarded for participation in specific tags.

Methodenspezifische Parameter: `inname: "string"`
; sort: rank, name

### `GET /users/{ids}/badges`

Get the badges the users in {ids} have earned.

Methodenspezifische Parameter: `ids: "number list"`
; sort: rank, name, type, awarded

### `GET /badges`

Returns all the badges in the system.

Methodenspezifische Parameter: `inname: "string"`
; sort: rank, name, type

### `GET /collectives/{slugs}`

Returns Collective objects representing the Collectives in {slugs} found on the site.

Methodenspezifische Parameter: `slugs: "string list"`
; sort: name

### `GET /collectives`

Returns all Collectives in the system.
; sort: name

### `GET /comments/{id}/flags/options` (access_token)

Returns the different flags that the user identified with an access_token can create for the comment identified by {id}. Available flags vary from comment to comment and user to user, an app should never assume a particular flag can be created without consulting this method.

Methodenspezifische Parameter: `id: "number"`

### `GET /comments/{ids}`

Gets the comments identified in id.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, votes

### `GET /users/{ids}/comments/{toid}`

Get the comments that the users in {ids} have posted in reply to the single user identified in {toid}.

Methodenspezifische Parameter: `ids: "number list", toid: "number"`
; sort: creation, votes

### `GET /answers/{ids}/comments`

Gets the comments on a set of answers.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, votes

### `GET /posts/{ids}/comments`

Gets the comments on the posts identified in ids, regardless of the type of the posts.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, votes

### `GET /questions/{ids}/comments`

Gets the comments on a question.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, votes

### `GET /users/{ids}/comments`

Get the comments posted by users in {ids}.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, votes

### `GET /comments`

Gets all the comments on the site.
; sort: creation, votes

### `GET /filters/create`

Creates a new filter given a list of includes, excludes, a base filter, and whether or not this filter should be "unsafe".

Methodenspezifische Parameter: `include: "string list", exclude: "string list", base: "string", unsafe: ["false", "true"]`

### `GET /users/moderators/elected`

Returns those users on a site who both have moderator powers, and were actually elected.
; sort: reputation, creation, name, modified

### `GET /errors`

Returns the various error codes that can be produced by the API.

### `GET /events` (access_token)

Returns a stream of events that have occurred on the site.

Methodenspezifische Parameter: `since: "date"`

### `GET /search/excerpts`

Searches a site for items which match the given criteria.

Methodenspezifische Parameter: `q: "string", accepted: ["", "True", "False"], answers: "number", body: "string", closed: ["", "True", "False"], migrated: ["", "True", "False"], notice: ["", "True", "False"], nottagged: "string list", tagged: "string list", title: "string", user: "number", url: "string", views: "number", wiki: ["", "True", "False"]`
; sort: activity, votes, creation, relevance

### `GET /tags/{tags}/faq`

Returns the frequently asked questions for the given set of tags in {tags}.

Methodenspezifische Parameter: `tags: "string list"`

### `GET /users/{ids}/favorites`

Get the questions that users in {ids} have bookmarked.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation, added

### `GET /users/{ids}/questions/featured`

Gets the questions on which the users in {ids} have active bounties.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /questions/featured`

Returns all the questions with active bounties in the system.

Methodenspezifische Parameter: `tagged: "string list"`
; sort: activity, votes, creation

### `GET /users/{id}/reputation-history/full` (access_token)

Returns a user's full reputation history, including private events.

Methodenspezifische Parameter: `scope: "private_info", id: "number"`

### `GET /inbox/unread` (access_token)

Returns the unread items in a user's inbox.

Methodenspezifische Parameter: `scope: "read_inbox", since: "date"`

### `GET /inbox` (access_token)

Returns a user's inbox.

Methodenspezifische Parameter: `scope: "read_inbox"`

### `GET /info`

Returns a collection of statistics about the site.

### `GET /access-tokens/{accessTokens}/invalidate`

Immediately expires the access tokens passed. This method is meant to allow an application to discard any active access tokens it no longer needs.

Methodenspezifische Parameter: `accessTokens: "string list"`

### `GET /questions/{ids}/linked`

Gets questions which link to those questions identified in {ids}.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation, rank

### `GET /me/achievements` (access_token)

Returns a user's recent network-wide achievements, given an access_token.

Methodenspezifische Parameter: `scope: "private_info"`

### `GET /me/answers` (access_token)

Returns the answers owned by the user associated with the given access_token.
; sort: activity, creation, votes

### `GET /me/associated` (access_token)

Returns all of a user's associated accounts, given an access_token for them.

Methodenspezifische Parameter: `types: "string"`

### `GET /me/badges` (access_token)

Returns the badges earned by the user associated with the given access_token.
; sort: rank, name, type

### `GET /me/comments/{toId}` (access_token)

Returns the comments owned by the user associated with the given access_token that are in reply to the user identified by {toId}.

Methodenspezifische Parameter: `toId: "number"`
; sort: creation, votes

### `GET /me/comments` (access_token)

Returns the comments owned by the user associated with the given access_token.
; sort: creation, votes

### `GET /me/favorites` (access_token)

Returns the questions bookmarked (previously known as "favorited") by the user associated with the given access_token.
; sort: activity, votes, creation, added

### `GET /me/questions/featured` (access_token)

Returns the questions that have active bounties offered by the user associated with the given access_token.
; sort: activity, votes, creation

### `GET /me/reputation-history/full` (access_token)

Returns user's full reputation history, including private events.

Methodenspezifische Parameter: `scope: "private_info"`

### `GET /me/inbox` (access_token)

Returns the user identified by access_token's inbox.

Methodenspezifische Parameter: `scope: "read_inbox"`

### `GET /me/mentioned` (access_token)

Returns the comments mentioning the user associated with the given access_token.
; sort: creation, votes

### `GET /me/merges` (access_token)

Returns a record of merges that have occurred involving a user identified by an access_token.

### `GET /me/network-activity` (access_token)

Returns a summary of a user's activity across the Stack Exchange network, given an access_token for them.

Methodenspezifische Parameter: `types: "string"`

### `GET /me/questions/no-answers` (access_token)

Returns the questions owned by the user associated with the given access_token that have no answers.
; sort: activity, votes, creation

### `GET /me/notifications` (access_token)

Returns a user's notifications, given an access_token.

Methodenspezifische Parameter: `scope: "read_inbox"`

### `GET /me/posts` (access_token)

Returns the posts owned by the user associated with the given access_token.
; sort: activity, creation, votes

### `GET /me/privileges` (access_token)

Returns the privileges the user identified by access_token has.

### `GET /me/questions` (access_token)

Returns the questions owned by the user associated with the given access_token.
; sort: activity, votes, creation

### `GET /me/reputation-history` (access_token)

Returns user's public reputation history.

### `GET /me/reputation` (access_token)

Returns the reputation changed for the user associated with the given access_token.

### `GET /me/suggested-edits` (access_token)

Returns the suggested edits the user identified by access_token has submitted.
; sort: creation, approval, rejection

### `GET /me/tag-preferences` (access_token)

Returns the tag preferences for the user associated with a given access_token.

Methodenspezifische Parameter: `scope: "private_info", id: "number"`

### `GET /me/tags/{tags}/top-answers` (access_token)

Returns the top 30 answers the user associated with the given access_token has posted in response to questions with the given tags.

Methodenspezifische Parameter: `tags: "string list"`
; sort: activity, creation, votes

### `GET /me/tags/{tags}/top-questions` (access_token)

Returns the top 30 questions the user associated with the given access_token has posted in response to questions with the given tags.

Methodenspezifische Parameter: `tags: "string list"`
; sort: activity, votes, creation, hot, week, month, relevance

### `GET /me/tags` (access_token)

Returns the tags the user identified by the access_token passed is active in.
; sort: popular, activity, name

### `GET /me/timeline` (access_token)

Returns a subset of the actions the user identified by the passed access_token has taken on the site.

### `GET /me/top-answer-tags` (access_token)

Returns the user identified by access_token's top 30 tags by answer score.

### `GET /me/top-question-tags` (access_token)

Returns the user identified by access_token's top 30 tags by question score.

### `GET /me/top-tags` (access_token)

Returns the user identified by access_token's top 30 tags by combined question and answer score.

### `GET /me/questions/unaccepted` (access_token)

Returns the questions owned by the user associated with the given access_token that have no accepted answer.
; sort: activity, votes, creation

### `GET /me/questions/unanswered` (access_token)

Returns the questions owned by the user associated with the given access_token that are not considered answered.
; sort: activity, votes, creation

### `GET /me/inbox/unread` (access_token)

Returns the unread items in the user identified by access_token's inbox.

Methodenspezifische Parameter: `scope: "read_inbox", since: "date"`

### `GET /me/notifications/unread` (access_token)

Returns a user's unread notifications, given an access_token.

Methodenspezifische Parameter: `scope: "read_inbox"`

### `GET /me` (access_token)

Returns the user associated with the passed access_token.
; sort: reputation, creation, name, modified

### `GET /users/{ids}/mentioned`

Gets all the comments that the users in {ids} were mentioned in.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, votes

### `GET /users/{ids}/merges`

Returns a record of merges that have occurred involving the passed account ids.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /tags/moderator-only`

Returns the tags found on a site that only moderators can use.

Methodenspezifische Parameter: `inname: "string"`
; sort: popular, activity, name

### `GET /users/moderators`

Gets those users on a site who can exercise moderation powers.
; sort: reputation, creation, name, modified

### `GET /users/{ids}/questions/no-answers`

Gets the questions asked by the users in {ids} which have no answers.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /questions/no-answers`

Returns questions which have received no answers.

Methodenspezifische Parameter: `tagged: "string list"`
; sort: activity, votes, creation

### `GET /notifications` (access_token)

Returns a user's notifications.

Methodenspezifische Parameter: `scope: "read_inbox"`

### `GET /posts/{ids}`

Fetches a set of posts by ids.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, creation, votes

### `GET /posts/{ids}/suggested-edits`

Returns suggested edits on the posts identified in ids.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, approval, rejection

### `GET /users/{ids}/posts`

Returns the posts the users in {ids} have posted.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, creation, votes

### `GET /posts`

Fetches all posts (questions and answers) on the site.
; sort: activity, creation, votes

### `GET /users/{id}/privileges`

Returns the privileges a user has.

Methodenspezifische Parameter: `id: "number"`

### `GET /privileges`

Returns the earnable privileges on a site.

### `GET /questions/{id}/close/options` (access_token)

Returns the flag options that make up close reasons that the user identified with an access_token can create for this question. Available flags vary from post to post and user to user, an app should never assume a particular flag can be created without consulting this method.

Methodenspezifische Parameter: `id: "number"`

### `GET /questions/{id}/flags/options` (access_token)

Returns the different flags, including close reasons, that the user identified with an access_token can create for this question. Available flags vary from post to post and user to user, an app should never assume a particular flag can be created without consulting this method.

Methodenspezifische Parameter: `id: "number"`

### `GET /answers/{ids}/questions`

Returns the questions that answers identied by {ids} are on.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /collectives/{slugs}/questions`

Returns the questions that are part of the Collective identified by {slugs}.

Methodenspezifische Parameter: `slugs: "string list"`
; sort: activity, votes, creation

### `GET /questions/{ids}`

Returns the questions identified in {ids}.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /users/{ids}/questions`

Gets the questions asked by the users in {ids}.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /questions/{ids}/timeline`

Returns a subset of the events that have happened to the questions identified in id.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /questions`

Gets all the questions on the site.

Methodenspezifische Parameter: `tagged: "string list"`
; sort: activity, votes, creation, hot, week, month

### `GET /access-tokens/{accessTokens}`

Reads the properties for a set of access tokens.

Methodenspezifische Parameter: `accessTokens: "string list"`

### `GET /filters/{filters}`

Returns the fields included by the given filters, and the "safeness" of those filters.

Methodenspezifische Parameter: `filters: "string list"`

### `GET /questions/{ids}/related`

Returns questions that the site considers related to those identified in {ids}.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation, rank

### `GET /tags/{tags}/related`

Returns the tags that are most related to those in {tags}.

Methodenspezifische Parameter: `tags: "string list"`

### `GET /users/{ids}/reputation-history`

Returns users' public reputation history.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /users/{ids}/reputation`

Gets a subset of the reputation changes for users in {ids}.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /tags/required`

Returns the tags found on a site that fulfill required tag constraints on questions.

Methodenspezifische Parameter: `inname: "string"`
; sort: popular, activity, name

### `GET /revisions/{ids}`

Returns edit revisions identified by ids in {ids}.

Methodenspezifische Parameter: `ids: "guid list"`

### `GET /posts/{ids}/revisions`

Returns edit revisions for the posts identified in ids.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /search`

Searches a site for any questions which fit the given criteria.

Methodenspezifische Parameter: `tagged: "string list", nottagged: "string list", intitle: "string"`
; sort: activity, votes, creation, relevance

### `GET /similar`

Returns questions which are similar to a hypothetical one based on a title and tag combination.

Methodenspezifische Parameter: `tagged: "string list", nottagged: "string list", title: "string"`
; sort: activity, votes, creation, relevance

### `GET /errors/{id}`

This method allows you to generate an error.

Methodenspezifische Parameter: `id: "number"`

### `GET /sites`

Returns all sites in the network.

### `GET /suggested-edits/{ids}`

Returns suggested edits identified in ids.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, approval, rejection

### `GET /users/{ids}/suggested-edits`

Returns the suggested edits that the users in {ids} have submitted.

Methodenspezifische Parameter: `ids: "number list"`
; sort: creation, approval, rejection

### `GET /suggested-edits`

Returns all the suggested edits in the systems.
; sort: creation, approval, rejection

### `GET /tags/{tags}/synonyms`

Gets all the synonyms that point to the tags identified in {tags}. If you're looking to discover all the tag synonyms on a site, use the /tags/synonyms methods instead of call this method on all tags.

Methodenspezifische Parameter: `tags: "string list"`
; sort: creation, applied, activity

### `GET /users/{id}/tag-preferences` (access_token)

Returns the given user's tag preferences.

Methodenspezifische Parameter: `scope: "private_info", id: "number"`

### `GET /tags/synonyms`

Returns all tag synonyms found on the site.
; sort: creation, applied, activity

### `GET /collectives/{slugs}/tags`

Returns tag objects belonging to the Collectives in {slugs} found on the site.

Methodenspezifische Parameter: `slugs: "string list"`
; sort: popular, activity, name

### `GET /tags/{tags}/info`

Returns tag objects representing the tags in {tags} found on the site.

Methodenspezifische Parameter: `tags: "string list"`
; sort: popular, activity, name

### `GET /users/{ids}/tags`

Returns the tags the users identified in {ids} have been active in.

Methodenspezifische Parameter: `ids: "number list"`
; sort: popular, activity, name

### `GET /tags`

Returns the tags found on a site.

Methodenspezifische Parameter: `inname: "string"`
; sort: popular, activity, name

### `GET /users/{ids}/timeline`

Returns a subset of the actions the users in {ids} have taken on the site.

Methodenspezifische Parameter: `ids: "number list"`

### `GET /users/{id}/top-answer-tags`

Returns a single user's top tags by answer score.

Methodenspezifische Parameter: `id: "number"`

### `GET /tags/{tag}/top-answerers/{period}`

Returns the top 20 answerers active in a single tag, of either all-time or the last 30 days.

Methodenspezifische Parameter: `tag: "string", period: ["all_time", "month"]`

### `GET /tags/{tag}/top-askers/{period}`

Returns the top 20 askers active in a single tag, of either all-time or the last 30 days.

Methodenspezifische Parameter: `tag: "string", period: ["all_time", "month"]`

### `GET /users/{id}/top-question-tags`

Returns a single user's top tags by question score.

Methodenspezifische Parameter: `id: "number"`

### `GET /users/{id}/top-tags`

Returns a single user's top tags by combined question and answer score.

Methodenspezifische Parameter: `id: "number"`

### `GET /users/{id}/tags/{tags}/top-answers`

Returns the top 30 answers a user has posted in response to questions with the given tags.

Methodenspezifische Parameter: `id: "number", tags: "string list"`
; sort: activity, creation, votes

### `GET /users/{id}/tags/{tags}/top-questions`

Returns the top 30 questions a user has asked with the given tags.

Methodenspezifische Parameter: `id: "number", tags: "string list"`
; sort: activity, votes, creation

### `GET /users/{ids}/questions/unaccepted`

Gets the questions asked by the users in {ids} which have at least one answer, but no accepted answer.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /questions/unanswered/my-tags` (access_token)

Returns questions the site considers to be unanswered, which are within a user's favorite tags. If a user has not favorites, their frequented tags are used instead.
; sort: activity, votes, creation

### `GET /users/{ids}/questions/unanswered`

Gets the questions asked by the users in {ids} which the site considers unanswered, while still having at least one answer posted.

Methodenspezifische Parameter: `ids: "number list"`
; sort: activity, votes, creation

### `GET /questions/unanswered`

Returns questions the site considers to be unanswered.

Methodenspezifische Parameter: `tagged: "string list"`
; sort: activity, votes, creation

### `GET /notifications/unread` (access_token)

Returns a user's unread notifications.

Methodenspezifische Parameter: `scope: "read_inbox"`

### `GET /users/{id}/inbox` (access_token)

Returns a user's inbox.

Methodenspezifische Parameter: `scope: "read_inbox", id: "number"`

### `GET /users/{id}/notifications` (access_token)

Returns a user's notifications.

Methodenspezifische Parameter: `scope: "read_inbox", id: "number"`

### `GET /users/{id}/inbox/unread` (access_token)

Returns the unread items in a user's inbox.

Methodenspezifische Parameter: `scope: "read_inbox", id: "number", since: "date"`

### `GET /users/{id}/notifications/unread` (access_token)

Returns a user's unread notifications.

Methodenspezifische Parameter: `scope: "read_inbox", id: "number"`

### `GET /collectives/{slugs}/users`

Returns users objects who are members of the Collectives in {slugs}.

Methodenspezifische Parameter: `slugs: "string list"`
; sort: reputation, creation, name, modified

### `GET /users/{ids}`

Gets the users identified in ids in {ids}.

Methodenspezifische Parameter: `ids: "number list"`
; sort: reputation, creation, name, modified

### `GET /users/{id}/network-activity`

Returns a summary of a user's activity across the Stack Exchange network, given their account_id.

Methodenspezifische Parameter: `id: "number", types: "string"`

### `GET /users`

Returns all users on a site.

Methodenspezifische Parameter: `inname: "string"`
; sort: reputation, creation, name, modified

### `GET /tags/{tags}/wikis`

Returns the wikis that go with the given set of tags in {tags}.

Methodenspezifische Parameter: `tags: "string list"`


## POST-Methoden (35)

### `POST /answers/{id}/accept` (access_token)

Accepts an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /answers/{id}/flags/add` (access_token)

Casts a flag against the answer identified by id.

Methodenspezifische Parameter: `scope: "write_access", id: "number", option_id: "number", comment: "string"`

### `POST /answers/{id}/suggested-edit/add` (access_token)

Create a suggested_edit on an existing answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number", body: "string", comment: "string"`

### `POST /questions/{id}/answers/add` (access_token)

Create a new answer on the given question.

Methodenspezifische Parameter: `scope: "write_access", id: "number", body: "string"`

### `POST /comments/{id}/flags/add` (access_token)

Casts a flag against the comment identified by id.

Methodenspezifische Parameter: `scope: "write_access", id: "number", option_id: "number", comment: "string"`

### `POST /posts/{id}/comments/add` (access_token)

Create a new comment.

Methodenspezifische Parameter: `scope: "write_access", id: "number", body: "string"`

### `POST /questions/{id}/flags/add` (access_token)

Casts a flag (including "close votes") against the question identified by id.

Methodenspezifische Parameter: `scope: "write_access", id: "number", option_id: "number", comment: "string", target_site: "string", question_id: "number"`

### `POST /questions/{id}/suggested-edit/add` (access_token)

Create a suggested_edit on an existing question.

Methodenspezifische Parameter: `scope: "write_access", id: "number", title: "string", body: "string", tags: "string list", comment: "string"`

### `POST /questions/add` (access_token)

Create a new question.

Methodenspezifische Parameter: `scope: "write_access", title: "string", body: "string", tags: "string list"`

### `POST /answers/{id}/delete` (access_token)

Deletes an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /comments/{id}/delete` (access_token)

Deletes a comment.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /questions/{id}/delete` (access_token)

Deletes a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /answers/{id}/downvote` (access_token)

Downvotes an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /questions/{id}/downvote` (access_token)

Downvotes a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /answers/{id}/edit` (access_token)

Edit an existing answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number", body: "string", comment: "string"`

### `POST /comments/{id}/edit` (access_token)

Edit an existing comment.

Methodenspezifische Parameter: `scope: "write_access", id: "number", body: "string"`

### `POST /questions/{id}/edit` (access_token)

Edit an existing question.

Methodenspezifische Parameter: `scope: "write_access", id: "number", title: "string", body: "string", tags: "string list", comment: "string"`

### `POST /users/{id}/tag-preferences/edit` (access_token)

Edit a user's tag preferences.

Methodenspezifische Parameter: `scope: "write_access private_info", id: "number", favorite_tags: "string list", ignored_tags: "string list"`

### `POST /questions/{id}/favorite` (access_token)

Bookmarks a question. Previously known as "favoriting" a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /me/tag-preferences/edit` (access_token)

Edits the tag preferences of the user identified by the given access_token.

Methodenspezifische Parameter: `scope: "write_access private_info", favorite_tags: "string list", ignored_tags: "string list"`

### `POST /answers/{id}/recommend` (access_token)

Recommends an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number", slug: "key"`

### `POST /questions/{id}/answers/render`

Render an answer given it's body and the question it's on.

Methodenspezifische Parameter: `id: "number", body: "string"`

### `POST /posts/{id}/comments/render`

Render a comment given its body and the post it's on.

Methodenspezifische Parameter: `id: "number", body: "string"`

### `POST /questions/render`

Renders a question given it's fields.

Methodenspezifische Parameter: `title: "string", body: "string", tags: "string list"`

### `POST /answers/{id}/accept/undo` (access_token)

Undoes an accept on an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /answers/{id}/downvote/undo` (access_token)

Undoes an downvote on an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /questions/{id}/downvote/undo` (access_token)

Undoes an downvote on a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /question/{id}/favorite/undo` (access_token)

Unbookmarks a question. Previously known as "unfavoriting" a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /answers/{id}/recommend/undo` (access_token)

Recommends an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number", slug: "key"`

### `POST /answers/{id}/upvote/undo` (access_token)

Undoes an upvote on an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /comments/{id}/upvote/undo` (access_token)

Undoes an upvote on a comment.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /question/{id}/upvote/undo` (access_token)

Undoes an upvote on a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /answers/{id}/upvote` (access_token)

Upvotes an answer.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /comments/{id}/upvote` (access_token)

Upvotes a comment.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`

### `POST /questions/{id}/upvote` (access_token)

Upvotes a question.

Methodenspezifische Parameter: `scope: "write_access", id: "number"`
