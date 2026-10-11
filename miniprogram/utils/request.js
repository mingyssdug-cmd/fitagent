const BASE_URL = 'http://127.0.0.1:8000';

/**
 * 统一请求方法
 * @param {string} url 接口路径，如 /api/v1/auth/login
 * @param {object} data 请求体
 * @param {string} method 请求方法（GET/POST/PUT/DELETE）
 */
function request(url, data = {}, method = 'POST') {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (wx.getStorageSync('token') || ''),
      },
      timeout: 60000, // 60 秒超时（LLM 调用可能较慢）
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error('请求失败：' + res.statusCode));
        }
      },
      fail: (err) => reject(err),
    });
  });
}

module.exports = {
  request,
  BASE_URL,
};