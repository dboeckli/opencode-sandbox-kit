# Stack Exchange API (kompakt)

- **API-Version (`api_revision`)**: `2026.5.26.43284` (abgefragt 2026-08-11 via `GET /2.3/info?site=stackoverflow` → `items[0].api_revision`)
- **Basis-URL**: `https://api.stackexchange.com/2.3` · **Auth**: `Authorization: Bearer $STACKOVERFLOW_API_KEY`
- **Pflicht**: `site` (z. B. `stackoverflow`) bei fast allen Methoden; `access_token` = OAuth nötig
- **Detaillierte Doku mit allen Parametern**: `~/stackexchange-api-detail.md` · **Offiziell**: https://api.stackexchange.com/docs

## Generische Parameter (gelten fast überall)

| Param | Typ | Beschreibung |
|---|---|---|
| `site` | string | Site, z. B. `stackoverflow` (meist Pflicht) |
| `page` / `pagesize` | number | Pagination; 1-basiert, 1–100 (Default 30) |
| `fromdate` / `todate` | date | Unix-Timestamp-Filter |
| `order` | `desc`/`asc` | Sortierrichtung (Default `desc`) |
| `min` / `max` | depends | Grenzen für `sort`-Wert |
| `sort` | string | Sortierfeld, methodenspezifisch |
| `filter` | string | Custom-Filter (z. B. `!nNPvSNdWme`) |
| `key` | key | API-Key (hier via Proxy-Header) |
| `preview` | `true`/`false` | Write: simuliert ohne Ausführung |

**Antwort-Wrapper**: `{"items": [...], "has_more": bool, "quota_max": n, "quota_remaining": n}` — `page` erhöhen bis `has_more == false`.


## GET (142)

| Endpoint | Params (methodenspezifisch) | Beschreibung |
|---|---|---|
| `GET /access-tokens/{accessTokens}` | `accessTokens` | Reads the properties for a set of access tokens. |
| `GET /access-tokens/{accessTokens}/invalidate` | `accessTokens` | Immediately expires the access tokens passed. This method is meant to allow an applicatio… |
| `GET /answers` | `—` | Returns all the undeleted answers in the system. |
| `GET /answers/{ids}` | `ids` | Gets the set of answers identified by ids. |
| `GET /answers/{ids}/comments` | `ids` | Gets the comments on a set of answers. |
| `GET /answers/{ids}/questions` | `ids` | Returns the questions that answers identied by {ids} are on. |
| `GET /answers/{id}/flags/options` 🔑 | `id` | Returns the different flags that the user identified with an access_token can create for… |
| `GET /apps/{accessTokens}/de-authenticate` | `accessTokens` | Passing valid access_tokens to this method causes the application that created them to be… |
| `GET /badges` | `inname` | Returns all the badges in the system. |
| `GET /badges/name` | `inname` | Gets all explicitly named badges in the system. |
| `GET /badges/recipients` | `—` | Returns recently awarded badges in the system. |
| `GET /badges/tags` | `inname` | Returns the badges that are awarded for participation in specific tags. |
| `GET /badges/{ids}` | `ids` | Gets the badges identified in id. |
| `GET /badges/{ids}/recipients` | `ids` | Returns recently awarded badges in the system, constrained to a certain set of badges. |
| `GET /collectives` | `—` | Returns all Collectives in the system. |
| `GET /collectives/{slugs}` | `slugs` | Returns Collective objects representing the Collectives in {slugs} found on the site. |
| `GET /collectives/{slugs}/answers` | `slugs` | Returns answer objects belonging to Collectives in {slugs} found on the site. |
| `GET /collectives/{slugs}/questions` | `slugs` | Returns the questions that are part of the Collective identified by {slugs}. |
| `GET /collectives/{slugs}/tags` | `slugs` | Returns tag objects belonging to the Collectives in {slugs} found on the site. |
| `GET /collectives/{slugs}/users` | `slugs` | Returns users objects who are members of the Collectives in {slugs}. |
| `GET /comments` | `—` | Gets all the comments on the site. |
| `GET /comments/{ids}` | `ids` | Gets the comments identified in id. |
| `GET /comments/{id}/flags/options` 🔑 | `id` | Returns the different flags that the user identified with an access_token can create for… |
| `GET /errors` | `—` | Returns the various error codes that can be produced by the API. |
| `GET /errors/{id}` | `id` | This method allows you to generate an error. |
| `GET /events` 🔑 | `since` | Returns a stream of events that have occurred on the site. |
| `GET /filters/create` | `base, exclude, include, unsafe` | Creates a new filter given a list of includes, excludes, a base filter, and whether or no… |
| `GET /filters/{filters}` | `filters` | Returns the fields included by the given filters, and the "safeness" of those filters. |
| `GET /inbox` 🔑 | `scope` | Returns a user's inbox. |
| `GET /inbox/unread` 🔑 | `scope, since` | Returns the unread items in a user's inbox. |
| `GET /info` | `—` | Returns a collection of statistics about the site. |
| `GET /me` 🔑 | `—` | Returns the user associated with the passed access_token. |
| `GET /me/achievements` 🔑 | `scope` | Returns a user's recent network-wide achievements, given an access_token. |
| `GET /me/answers` 🔑 | `—` | Returns the answers owned by the user associated with the given access_token. |
| `GET /me/associated` 🔑 | `types` | Returns all of a user's associated accounts, given an access_token for them. |
| `GET /me/badges` 🔑 | `—` | Returns the badges earned by the user associated with the given access_token. |
| `GET /me/comments` 🔑 | `—` | Returns the comments owned by the user associated with the given access_token. |
| `GET /me/comments/{toId}` 🔑 | `toId` | Returns the comments owned by the user associated with the given access_token that are in… |
| `GET /me/favorites` 🔑 | `—` | Returns the questions bookmarked (previously known as "favorited") by the user associated… |
| `GET /me/inbox` 🔑 | `scope` | Returns the user identified by access_token's inbox. |
| `GET /me/inbox/unread` 🔑 | `scope, since` | Returns the unread items in the user identified by access_token's inbox. |
| `GET /me/mentioned` 🔑 | `—` | Returns the comments mentioning the user associated with the given access_token. |
| `GET /me/merges` 🔑 | `—` | Returns a record of merges that have occurred involving a user identified by an access_to… |
| `GET /me/network-activity` 🔑 | `types` | Returns a summary of a user's activity across the Stack Exchange network, given an access… |
| `GET /me/notifications` 🔑 | `scope` | Returns a user's notifications, given an access_token. |
| `GET /me/notifications/unread` 🔑 | `scope` | Returns a user's unread notifications, given an access_token. |
| `GET /me/posts` 🔑 | `—` | Returns the posts owned by the user associated with the given access_token. |
| `GET /me/privileges` 🔑 | `—` | Returns the privileges the user identified by access_token has. |
| `GET /me/questions` 🔑 | `—` | Returns the questions owned by the user associated with the given access_token. |
| `GET /me/questions/featured` 🔑 | `—` | Returns the questions that have active bounties offered by the user associated with the g… |
| `GET /me/questions/no-answers` 🔑 | `—` | Returns the questions owned by the user associated with the given access_token that have… |
| `GET /me/questions/unaccepted` 🔑 | `—` | Returns the questions owned by the user associated with the given access_token that have… |
| `GET /me/questions/unanswered` 🔑 | `—` | Returns the questions owned by the user associated with the given access_token that are n… |
| `GET /me/reputation` 🔑 | `—` | Returns the reputation changed for the user associated with the given access_token. |
| `GET /me/reputation-history` 🔑 | `—` | Returns user's public reputation history. |
| `GET /me/reputation-history/full` 🔑 | `scope` | Returns user's full reputation history, including private events. |
| `GET /me/suggested-edits` 🔑 | `—` | Returns the suggested edits the user identified by access_token has submitted. |
| `GET /me/tag-preferences` 🔑 | `id, scope` | Returns the tag preferences for the user associated with a given access_token. |
| `GET /me/tags` 🔑 | `—` | Returns the tags the user identified by the access_token passed is active in. |
| `GET /me/tags/{tags}/top-answers` 🔑 | `tags` | Returns the top 30 answers the user associated with the given access_token has posted in… |
| `GET /me/tags/{tags}/top-questions` 🔑 | `tags` | Returns the top 30 questions the user associated with the given access_token has posted i… |
| `GET /me/timeline` 🔑 | `—` | Returns a subset of the actions the user identified by the passed access_token has taken… |
| `GET /me/top-answer-tags` 🔑 | `—` | Returns the user identified by access_token's top 30 tags by answer score. |
| `GET /me/top-question-tags` 🔑 | `—` | Returns the user identified by access_token's top 30 tags by question score. |
| `GET /me/top-tags` 🔑 | `—` | Returns the user identified by access_token's top 30 tags by combined question and answer… |
| `GET /notifications` 🔑 | `scope` | Returns a user's notifications. |
| `GET /notifications/unread` 🔑 | `scope` | Returns a user's unread notifications. |
| `GET /posts` | `—` | Fetches all posts (questions and answers) on the site. |
| `GET /posts/{ids}` | `ids` | Fetches a set of posts by ids. |
| `GET /posts/{ids}/comments` | `ids` | Gets the comments on the posts identified in ids, regardless of the type of the posts. |
| `GET /posts/{ids}/revisions` | `ids` | Returns edit revisions for the posts identified in ids. |
| `GET /posts/{ids}/suggested-edits` | `ids` | Returns suggested edits on the posts identified in ids. |
| `GET /privileges` | `—` | Returns the earnable privileges on a site. |
| `GET /questions` | `tagged` | Gets all the questions on the site. |
| `GET /questions/featured` | `tagged` | Returns all the questions with active bounties in the system. |
| `GET /questions/no-answers` | `tagged` | Returns questions which have received no answers. |
| `GET /questions/unanswered` | `tagged` | Returns questions the site considers to be unanswered. |
| `GET /questions/unanswered/my-tags` 🔑 | `—` | Returns questions the site considers to be unanswered, which are within a user's favorite… |
| `GET /questions/{ids}` | `ids` | Returns the questions identified in {ids}. |
| `GET /questions/{ids}/answers` | `ids` | Gets the answers to a set of questions identified in id. |
| `GET /questions/{ids}/comments` | `ids` | Gets the comments on a question. |
| `GET /questions/{ids}/linked` | `ids` | Gets questions which link to those questions identified in {ids}. |
| `GET /questions/{ids}/related` | `ids` | Returns questions that the site considers related to those identified in {ids}. |
| `GET /questions/{ids}/timeline` | `ids` | Returns a subset of the events that have happened to the questions identified in id. |
| `GET /questions/{id}/close/options` 🔑 | `id` | Returns the flag options that make up close reasons that the user identified with an acce… |
| `GET /questions/{id}/flags/options` 🔑 | `id` | Returns the different flags, including close reasons, that the user identified with an ac… |
| `GET /revisions/{ids}` | `ids` | Returns edit revisions identified by ids in {ids}. |
| `GET /search` | `intitle, nottagged, tagged` | Searches a site for any questions which fit the given criteria. |
| `GET /search/advanced` | `accepted, answers, body, closed, migrated, notice, nottagged, q, tagged, title, url, user, views, wiki` | Searches a site for any questions which fit the given criteria. |
| `GET /search/excerpts` | `accepted, answers, body, closed, migrated, notice, nottagged, q, tagged, title, url, user, views, wiki` | Searches a site for items which match the given criteria. |
| `GET /similar` | `nottagged, tagged, title` | Returns questions which are similar to a hypothetical one based on a title and tag combin… |
| `GET /sites` | `—` | Returns all sites in the network. |
| `GET /suggested-edits` | `—` | Returns all the suggested edits in the systems. |
| `GET /suggested-edits/{ids}` | `ids` | Returns suggested edits identified in ids. |
| `GET /tags` | `inname` | Returns the tags found on a site. |
| `GET /tags/moderator-only` | `inname` | Returns the tags found on a site that only moderators can use. |
| `GET /tags/required` | `inname` | Returns the tags found on a site that fulfill required tag constraints on questions. |
| `GET /tags/synonyms` | `—` | Returns all tag synonyms found on the site. |
| `GET /tags/{tags}/faq` | `tags` | Returns the frequently asked questions for the given set of tags in {tags}. |
| `GET /tags/{tags}/info` | `tags` | Returns tag objects representing the tags in {tags} found on the site. |
| `GET /tags/{tags}/related` | `tags` | Returns the tags that are most related to those in {tags}. |
| `GET /tags/{tags}/synonyms` | `tags` | Gets all the synonyms that point to the tags identified in {tags}. If you're looking to d… |
| `GET /tags/{tags}/wikis` | `tags` | Returns the wikis that go with the given set of tags in {tags}. |
| `GET /tags/{tag}/top-answerers/{period}` | `period, tag` | Returns the top 20 answerers active in a single tag, of either all-time or the last 30 da… |
| `GET /tags/{tag}/top-askers/{period}` | `period, tag` | Returns the top 20 askers active in a single tag, of either all-time or the last 30 days. |
| `GET /users` | `inname` | Returns all users on a site. |
| `GET /users/moderators` | `—` | Gets those users on a site who can exercise moderation powers. |
| `GET /users/moderators/elected` | `—` | Returns those users on a site who both have moderator powers, and were actually elected. |
| `GET /users/{ids}` | `ids` | Gets the users identified in ids in {ids}. |
| `GET /users/{ids}/answers` | `ids` | Returns the answers the users in {ids} have posted. |
| `GET /users/{ids}/associated` | `ids, types` | Returns all of a user's associated accounts, given their account_ids in {ids}. |
| `GET /users/{ids}/badges` | `ids` | Get the badges the users in {ids} have earned. |
| `GET /users/{ids}/comments` | `ids` | Get the comments posted by users in {ids}. |
| `GET /users/{ids}/comments/{toid}` | `ids, toid` | Get the comments that the users in {ids} have posted in reply to the single user identifi… |
| `GET /users/{ids}/favorites` | `ids` | Get the questions that users in {ids} have bookmarked. |
| `GET /users/{ids}/mentioned` | `ids` | Gets all the comments that the users in {ids} were mentioned in. |
| `GET /users/{ids}/merges` | `ids` | Returns a record of merges that have occurred involving the passed account ids. |
| `GET /users/{ids}/posts` | `ids` | Returns the posts the users in {ids} have posted. |
| `GET /users/{ids}/questions` | `ids` | Gets the questions asked by the users in {ids}. |
| `GET /users/{ids}/questions/featured` | `ids` | Gets the questions on which the users in {ids} have active bounties. |
| `GET /users/{ids}/questions/no-answers` | `ids` | Gets the questions asked by the users in {ids} which have no answers. |
| `GET /users/{ids}/questions/unaccepted` | `ids` | Gets the questions asked by the users in {ids} which have at least one answer, but no acc… |
| `GET /users/{ids}/questions/unanswered` | `ids` | Gets the questions asked by the users in {ids} which the site considers unanswered, while… |
| `GET /users/{ids}/reputation` | `ids` | Gets a subset of the reputation changes for users in {ids}. |
| `GET /users/{ids}/reputation-history` | `ids` | Returns users' public reputation history. |
| `GET /users/{ids}/suggested-edits` | `ids` | Returns the suggested edits that the users in {ids} have submitted. |
| `GET /users/{ids}/tags` | `ids` | Returns the tags the users identified in {ids} have been active in. |
| `GET /users/{ids}/timeline` | `ids` | Returns a subset of the actions the users in {ids} have taken on the site. |
| `GET /users/{id}/achievements` 🔑 | `id, scope` | Returns a user's recent network-wide achievements, given their account id. |
| `GET /users/{id}/inbox` 🔑 | `id, scope` | Returns a user's inbox. |
| `GET /users/{id}/inbox/unread` 🔑 | `id, scope, since` | Returns the unread items in a user's inbox. |
| `GET /users/{id}/network-activity` | `id, types` | Returns a summary of a user's activity across the Stack Exchange network, given their acc… |
| `GET /users/{id}/notifications` 🔑 | `id, scope` | Returns a user's notifications. |
| `GET /users/{id}/notifications/unread` 🔑 | `id, scope` | Returns a user's unread notifications. |
| `GET /users/{id}/privileges` | `id` | Returns the privileges a user has. |
| `GET /users/{id}/reputation-history/full` 🔑 | `id, scope` | Returns a user's full reputation history, including private events. |
| `GET /users/{id}/tag-preferences` 🔑 | `id, scope` | Returns the given user's tag preferences. |
| `GET /users/{id}/tags/{tags}/top-answers` | `id, tags` | Returns the top 30 answers a user has posted in response to questions with the given tags. |
| `GET /users/{id}/tags/{tags}/top-questions` | `id, tags` | Returns the top 30 questions a user has asked with the given tags. |
| `GET /users/{id}/top-answer-tags` | `id` | Returns a single user's top tags by answer score. |
| `GET /users/{id}/top-question-tags` | `id` | Returns a single user's top tags by question score. |
| `GET /users/{id}/top-tags` | `id` | Returns a single user's top tags by combined question and answer score. |


## POST (35)

| Endpoint | Params (methodenspezifisch) | Beschreibung |
|---|---|---|
| `POST /answers/{id}/accept` 🔑 | `id, scope` | Accepts an answer. |
| `POST /answers/{id}/accept/undo` 🔑 | `id, scope` | Undoes an accept on an answer. |
| `POST /answers/{id}/delete` 🔑 | `id, scope` | Deletes an answer. |
| `POST /answers/{id}/downvote` 🔑 | `id, scope` | Downvotes an answer. |
| `POST /answers/{id}/downvote/undo` 🔑 | `id, scope` | Undoes an downvote on an answer. |
| `POST /answers/{id}/edit` 🔑 | `body, comment, id, scope` | Edit an existing answer. |
| `POST /answers/{id}/flags/add` 🔑 | `comment, id, option_id, scope` | Casts a flag against the answer identified by id. |
| `POST /answers/{id}/recommend` 🔑 | `id, scope, slug` | Recommends an answer. |
| `POST /answers/{id}/recommend/undo` 🔑 | `id, scope, slug` | Recommends an answer. |
| `POST /answers/{id}/suggested-edit/add` 🔑 | `body, comment, id, scope` | Create a suggested_edit on an existing answer. |
| `POST /answers/{id}/upvote` 🔑 | `id, scope` | Upvotes an answer. |
| `POST /answers/{id}/upvote/undo` 🔑 | `id, scope` | Undoes an upvote on an answer. |
| `POST /comments/{id}/delete` 🔑 | `id, scope` | Deletes a comment. |
| `POST /comments/{id}/edit` 🔑 | `body, id, scope` | Edit an existing comment. |
| `POST /comments/{id}/flags/add` 🔑 | `comment, id, option_id, scope` | Casts a flag against the comment identified by id. |
| `POST /comments/{id}/upvote` 🔑 | `id, scope` | Upvotes a comment. |
| `POST /comments/{id}/upvote/undo` 🔑 | `id, scope` | Undoes an upvote on a comment. |
| `POST /me/tag-preferences/edit` 🔑 | `favorite_tags, ignored_tags, scope` | Edits the tag preferences of the user identified by the given access_token. |
| `POST /posts/{id}/comments/add` 🔑 | `body, id, scope` | Create a new comment. |
| `POST /posts/{id}/comments/render` | `body, id` | Render a comment given its body and the post it's on. |
| `POST /question/{id}/favorite/undo` 🔑 | `id, scope` | Unbookmarks a question. Previously known as "unfavoriting" a question. |
| `POST /question/{id}/upvote/undo` 🔑 | `id, scope` | Undoes an upvote on a question. |
| `POST /questions/add` 🔑 | `body, scope, tags, title` | Create a new question. |
| `POST /questions/render` | `body, tags, title` | Renders a question given it's fields. |
| `POST /questions/{id}/answers/add` 🔑 | `body, id, scope` | Create a new answer on the given question. |
| `POST /questions/{id}/answers/render` | `body, id` | Render an answer given it's body and the question it's on. |
| `POST /questions/{id}/delete` 🔑 | `id, scope` | Deletes a question. |
| `POST /questions/{id}/downvote` 🔑 | `id, scope` | Downvotes a question. |
| `POST /questions/{id}/downvote/undo` 🔑 | `id, scope` | Undoes an downvote on a question. |
| `POST /questions/{id}/edit` 🔑 | `body, comment, id, scope, tags, title` | Edit an existing question. |
| `POST /questions/{id}/favorite` 🔑 | `id, scope` | Bookmarks a question. Previously known as "favoriting" a question. |
| `POST /questions/{id}/flags/add` 🔑 | `comment, id, option_id, question_id, scope, target_site` | Casts a flag (including "close votes") against the question identified by id. |
| `POST /questions/{id}/suggested-edit/add` 🔑 | `body, comment, id, scope, tags, title` | Create a suggested_edit on an existing question. |
| `POST /questions/{id}/upvote` 🔑 | `id, scope` | Upvotes a question. |
| `POST /users/{id}/tag-preferences/edit` 🔑 | `favorite_tags, id, ignored_tags, scope` | Edit a user's tag preferences. |
