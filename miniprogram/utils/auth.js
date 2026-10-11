const TOKEN_KEY = 'token';
const USER_KEY = 'user_info';

/**
 * 保存登录态
 * @param {string} token JWT token
 * @param {object} userInfo 用户信息 {user_id, name, phone}
 */
function setLogin(token, userInfo) {
  wx.setStorageSync(TOKEN_KEY, token);
  wx.setStorageSync(USER_KEY, userInfo);
}

/**
 * 获取 token
 */
function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || '';
}

/**
 * 获取用户信息
 */
function getUserInfo() {
  return wx.getStorageSync(USER_KEY) || null;
}

/**
 * 是否已登录
 */
function isLoggedIn() {
  return !!getToken();
}

/**
 * 清空登录态（退出登录）
 */
function clearLogin() {
  wx.removeStorageSync(TOKEN_KEY);
  wx.removeStorageSync(USER_KEY);
}

module.exports = {
  setLogin,
  getToken,
  getUserInfo,
  isLoggedIn,
  clearLogin,
};