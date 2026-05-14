function ok(res, data = null, message = null, status = 200) {
  const body = { success: true };
  if (message) body.message = message;
  if (data !== undefined && data !== null) body.data = data;
  return res.status(status).json(body);
}

function fail(res, message, status = 400, errors = null) {
  const body = { success: false, message };
  if (errors) body.errors = errors;
  return res.status(status).json(body);
}

module.exports = { ok, fail };
