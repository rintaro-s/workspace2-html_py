Rails.application.routes.draw do
  # 互換API
  post '/api.cgi', to: 'api#handle_request'
  # ファイル配信
  get '/files/*path', to: 'files#serve'
  # 互換: /file/:filename (旧クライアントが参照する可能性)
  get '/file/:filename', to: 'files#serve_single'
  # 健康チェック
  get '/up', to: proc { [200, { 'Content-Type' => 'text/plain' }, ['ok']] }
end
