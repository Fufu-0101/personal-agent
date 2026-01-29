<template>
  <div id="app">
    <ChatView />
  </div>
</template>

<script setup>
import ChatView from './components/ChatView.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f5;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
