# API Structures

This document provides the mappings of the 3 different transport types/structures we intend to support in A2A and how these are defined. Though not officially a REST api, it is REST-like and is referred to as the A2A REST API for simplicity.

The urls are based off of:
JSONRPC: {root\_url}/ \- all urls are this
gRPC: :{root\_url}/a2a.A2AService/
REST: {root\_url}/

| Method |  | JSONRPC | gRPC | REST |
| :---- | :---- | :---- | :---- | :---- |
| tasks/get | URL |  | GetTask | /v1/tasks/{id} |
|  | Method Type | POST | POST | GET |
|  | Payload | id: string<br> metadata?: \[key: string\]: any<br> historyLength?: number | message GetTaskRequest {<br>   // name=tasks/{id}<br>   string name;<br>   int32 history\_length;<br> } |  name: string<br> historyLength?: number |
|  | Response | Task | Task | Task |
| task/cancel | URL |  | CancelTask | /v1/tasks/{id}:cancel |
|  | Method Type | POST | POST | POST |
|  | Payload | id: string<br> metadata?: \[key: string\]: any | message CancelTaskRequest{<br>   // name=tasks/{id}<br>   string name;<br> } | name: string  |
|  | Response | Task | Task | Task |
| message/send | URL |  | SendMessage | /v1/message:send |
|  | Method Type | POST | POST | POST |
|  | Payload | message: Message<br> configuration?: MessageSendConfiguration<br> metadata?: \[key: string\]: any | message SendMessageRequest {<br>   Message msg;<br>   SendMessageConfiguration configuration;<br> } | message: Message<br>configuration?: SendMessageConfiguration<br> metadata?: \[key: string\]: any |
|  | Response | Message \| Task | message SendMessageResponse {<br>   oneof payload {<br>     Task task;<br>     Message msg;<br>   }<br> } | {<br>   message?: Message<br>   task?: Task<br> } |
| message/stream | URL |  | SendStreamingMessage | /v1/message:stream |
|  | Method Type | POST | POST | POST |
|  | Payload | message: Message<br> configuration?: MessageSendConfiguration<br> metadata?: \[key: string\]: any | message SendMessageRequest {<br>   Message msg;<br>   SendMessageConfiguration configuration;<br> } | message: Message<br> configuration?: MessageSendConfiguration<br> metadata?: \[key: string\]: any |
|  | Response | Message \| Task \| TaskStatusUpdateEvent \| TaskArtifactUpdateEvent | message StreamResponse {<br>   oneof payload {<br>     Task task;<br>     Message msg;<br>     TaskStatusUpdateEvent status\_update;<br>     TaskArtifactUpdateEvent artifact\_update;<br>   }<br> } | {<br>   message?: Message<br>   task?: Task<br>   statusUpdate?: TaskStatusUpdateEvent<br>   artifactUpdate?: TaskArtifactUpdateEvent<br> } |
| tasks/resubscribe | URL |  | TaskSubscription | /v1/tasks/{id}:resubscribe |
|  | Method Type | POST | POST | POST |
|  | Payload | id: string<br> metadata?: \[key: string\]: any | message TaskSubscriptionRequest{<br>   // name=tasks/{id}<br>   string name;<br> } | name: string  |
|  | Response | Message \| Task \| TaskStatusUpdateEvent \| TaskArtifactUpdateEvent | message StreamResponse {<br>   oneof payload {<br>     Task task;<br>     Message msg;<br>     TaskStatusUpdateEvent status\_update;<br>     TaskArtifactUpdateEvent artifact\_update;<br>   }<br> } | {<br>   message?: Message<br>   task?: Task<br>   statusUpdate?: TaskStatusUpdateEvent<br>   artifactUpdate?: TaskArtifactUpdateEvent<br> } |
| tasks/pushNotificationConfig/get | URL |  | GetTaskPushNotification | /v1/tasks/\*/pushNotificationConfigs/\* |
|  | Method Type | POST | POST | GET |
|  | Payload | id: string<br> metadata?: \[key: string\]: any | message TaskSubscriptionRequest {<br>   // name=tasks/{id}/pushNotification/{id}<br>   string name;<br> } | name: string  |
|  | Response | TaskPushNotificationConfig | TaskPushNotificationConfig | TaskPushNotificationConfig |
| tasks/pushNotificationConfig/set | URL |  | CreateTaskPushNotification | /v1/tasks/{id}/pushNotificationConfigs |
|  | Method Type | POST | POST | POST |
|  | Payload | TaskPushNotificationConfig | message SetTaskPushNotificationRequest {<br>   TaskPushNotificationConfig config \= 1;<br> } | config: TaskPushNotificationConfig |
|  | Response | TaskPushNotificationConfig | TaskPushNotificationConfig | TaskPushNotificationConfig |
| card/get | URL | Not defined now | GetAgentCard | /v1/card |
|  | Method Type | POST | POST | GET |
|  | Payload | None | None | None |
|  | Response | AgentCard | AgentCard | AgentCard |
| List Task Notifications | URL | N/A | ListTaskPushNotification | /v1/tasks/{id}/pushNotificationConfigs |
|  | Method Type |  | GET | GET |
|  | Payload |  | message ListTaskPushNotificationRequest {<br>   // parent=tasks/{id}<br>   string parent \= 1;<br> } | parent: string |
|  | Response |  | repeated TaskPushNotificationConfig | \[TaskPushNotificationConfig\] |
| List Tasks | URL | N/A | ListTask | /v1/tasks |
|  | Method Type |  | GET | GET |
|  | Payload |  | {} | {} |
|  | Response |  | repeated Task | \[Task\] |

## Caveats

* The REST API defines a wrapper structure for the streaming responses. This is not the same as the JSONRPC approach.
* The push notification setter method has a wrapper class for the input payload for REST as well. This is intended to make this more consistent with the gRPC approach
* The metadata fields at the request level are overly broad and hard to utilize. Removed these in the gRPC version.
* The REST API is based on the transcoding and best practices as defined by AIP-127.
