### API Structures

This document provides the mappings of the 3 different transport types/structures we intend to support in A2A and how these are defined. Though not officially a REST api, it is REST-like and is referred to as the A2A REST API for simplicity.

The urls are based off of:  
JSONRPC: {root\_url}/ \- all urls are this  
gRPC: :{root\_url}/a2a.A2AService/  
REST: {root\_url}/

| Method |  | JSONRPC | gRPC | REST |
| :---- | :---- | :---- | :---- | :---- |
| tasks/get | URL |  | GetTask | /v1/tasks/{id} |
|  | Method Type | POST | POST | GET |
|  | Payload | id: string metadata?: \[key: string\]: any historyLength?: number | message GetTaskRequest {   // name=tasks/{id}   string name;   int32 history\_length; } |  name: string historyLength?: number |
|  | Response | Task | Task | Task |
| task/cancel | URL |  | CancelTask | /v1/tasks/{id}:cancel |
|  | Method Type | POST | POST | POST |
|  | Payload | id: string metadata?: \[key: string\]: any | message CancelTaskRequest{   // name=tasks/{id}   string name; } | name: string  |
|  | Response | Task | Task | Task |
| message/send | URL |  | SendMessage | /v1/message:send |
|  | Method Type | POST | POST | POST |
|  | Payload | message: Message configuration?: MessageSendConfiguration metadata?: \[key: string\]: any | message SendMessageRequest {   Message msg;   SendMessageConfiguration configuration; } | message: Message configuration?: SendMessageConfiguration metadata?: \[key: string\]: any |
|  | Response | Message | Task | message SendMessageResponse{   oneof payload {     Task task;     Message msg;   } } | {   message?: Message   task?: Task } |
| message/stream | URL |  | SendStreamingMessage | /v1/message:stream |
|  | Method Type | POST | POST | POST |
|  | Payload | message: Message configuration?: MessageSendConfiguration metadata?: \[key: string\]: any | message SendMessageRequest {   Message msg;   SendMessageConfiguration configuration; } | message: Message configuration?: MessageSendConfiguration metadata?: \[key: string\]: any |
|  | Response | Message | Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent | message StreamResponse {   oneof payload {     Task task;     Message msg;     TaskStatusUpdateEvent status\_update;     TaskArtifactUpdateEvent artifact\_update;   } } | {   message?: Message   task?: Task   statusUpdate?: TaskStatusUpdateEvent   artifactUpdate?: TaskArtifactUpdateEvent } |
| tasks/resubscribe | URL |  | TaskSubscription | /v1/tasks/{id}:resubscribe |
|  | Method Type | POST | POST | POST |
|  | Payload | id: string metadata?: \[key: string\]: any | message TaskSubscriptionRequest{   // name=tasks/{id}   string name; } | name: string  |
|  | Response | Message | Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent | message StreamResponse {   oneof payload {     Task task;     Message msg;     TaskStatusUpdateEvent status\_update;     TaskArtifactUpdateEvent artifact\_update;   } } | {   message?: Message   task?: Task   statusUpdate?: TaskStatusUpdateEvent   artifactUpdate?: TaskArtifactUpdateEvent } |
| tasks/pushNotificationConfig/get | URL |  | GetTaskPushNotification | /v1/tasks/\*/pushNotificationConfigs/\* |
|  | Method Type | POST | POST | GET |
|  | Payload | id: string metadata?: \[key: string\]: any | message TaskSubscriptionRequest{   // name=tasks/{id}/pushNotification/{id}   string name; } | name: string  |
|  | Response | TaskPushNotificationConfig | TaskPushNotificationConfig | TaskPushNotificationConfig |
| tasks/pushNotificationConfig/set | URL |  | CreateTaskPushNotification | /v1/tasks/{id}/pushNotificationConfigs |
|  | Method Type | POST | POST | POST |
|  | Payload | TaskPushNotificationConfig | message SetTaskPushNotificationRequest {   TaskPushNotificationConfig config \= 1; } | config: TaskPushNotificationConfig |
|  | Response | TaskPushNotificationConfig | TaskPushNotificationConfig | TaskPushNotificationConfig |
| card/get | URL | Not defined now | GetAgentCard | v1/card |
|  | Method Type | POST | POST | GET |
|  | Payload | None | None | None |
|  | Response | AgentCard | AgentCard | AgentCard |
| List Task Notifications | URL | N/A | ListTaskPushNotification | /v1/tasks/{id}/pushNotificationConfigs |
|  | Method Type |  | GET | GET |
|  | Payload |  | message ListTaskPushNotificationRequest {   // parent=tasks/{id}   string parent \= 1; } | parent: string |
|  | Response |  | repeated TaskPushNotificationConfig | \[TaskPushNotificationConfig\] |
| List Tasks | URL | N/A | ListTask | /v1/tasks |
|  | Method Type |  | GET | GET |
|  | Payload |  | {} | {} |
|  | Response |  | repeated Task | \[Task\] |

### Caveats

* The REST API defines a wrapper structure for the streaming responses. This is not the same as the JSONRPC approach. This aligns with the [discussion](https://discord.com/channels/1362108044737253548/1362204635347026100/1374496543482187902) on Discord \[[https://discord.com/channels/1362108044737253548/1362204635347026100/1374496543482187902](https://discord.com/channels/1362108044737253548/1362204635347026100/1374496543482187902)\]   
* The push notification setter method has a wrapper class for the input payload for REST as well. This is intended to make this more consistent with the gRPC approach  
* The metadata fields at the request level are overly broad and hard to utilize. Removed these in the gRPC version.  
* The REST API is based on the transcoding and best practices as defined by AIP-127. 
