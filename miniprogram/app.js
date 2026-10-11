App({
  globalData: {
    userInfo: null,
    token: null,
  },

  onLaunch() {
    // 启动时检查本地有没有 token
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('user_info');

    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      console.log('已登录，用户：', userInfo.name);
    } else {
      console.log('未登录，需要跳转到登录页');
    }
  },
});