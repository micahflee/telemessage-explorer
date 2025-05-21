import { createRouter, createWebHashHistory, type RouteRecordRaw } from "vue-router";
import GroupsView from "./views/GroupsView.vue";
import GroupView from "./views/GroupView.vue";
import UsersView from "./views/UsersView.vue";
import UserView from "./views/UserView.vue";
import MessagesView from "./views/MessagesView.vue";
import MessageView from "./views/MessageView.vue";

const routes: Array<RouteRecordRaw> = [
    {
        path: "/",
        name: "groups",
        component: GroupsView,
    },
    {
        path: "/groups/:groupId",
        name: "group",
        component: GroupView,
    },
    {
        path: "/users",
        name: "users",
        component: UsersView,
    },
    {
        path: "/users/:userId",
        name: "user",
        component: UserView,
    },
    {
        path: "/messages",
        name: "messages",
        component: MessagesView,
    },
    {
        path: "/messages/:messageId",
        name: "message",
        component: MessageView,
    },
];

const router = createRouter({
    history: createWebHashHistory(),
    routes,
});

export default router;
