require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.cache_classes = false
  config.eager_load = false
  config.consider_all_requests_local = true
  config.server_timing = true
  config.action_controller.enable_fragment_cache_logging = true
  config.active_support.deprecation = :log
  config.active_support.disallowed_deprecation = :raise
  config.active_support.disallowed_deprecation_warnings = []
  # In API-only apps or setups without the asset pipeline `config.assets` may be undefined.
  # Guard access so the environment file works across different Rails app types.
  if config.respond_to?(:assets)
    config.assets.quiet = true
  end
end
