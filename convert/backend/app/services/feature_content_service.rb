class FeatureContentService
  def initialize(user)
    @user = user
  end

  def add_subitem!(feature_id, name, type)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    content['subItems'] ||= {}
    sid = "#{type}_#{(Time.now.to_f*1000).to_i}"
    content['subItems'][sid] = { 'id' => sid, 'name' => name, 'type' => type, 'messages' => (type == 'channel' ? [] : []), 'posts' => (type == 'thread' ? [] : []) }
    fc.update_json!(content)
  end

  def add_whiteboard!(feature_id, name)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    content['boards'] ||= {}
    bid = "board_#{(Time.now.to_f*1000).to_i}"
    content['boards'][bid] = { 'id' => bid, 'name' => name, 'elements' => {}, 'created_by' => @user.username, 'created_at' => Time.now.to_f }
    fc.update_json!(content)
  end

  def save_whiteboard!(feature_id, board_id, elements)
    raise 'Feature ID, board ID, and elements are required' if feature_id.blank? || board_id.blank? || elements.blank?
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    boards = content['boards'] || {}
    raise 'Board not found' unless boards[board_id]
    boards[board_id]['elements'] = JSON.parse(elements)
    boards[board_id]['updated_at'] = Time.now.to_f
    fc.update_json!(content)
  end

  def post_message!(feature_id, sub_item_id, content_text)
    raise 'Feature ID, sub item ID, and content are required' if feature_id.blank? || sub_item_id.blank? || content_text.blank?
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    subitems = content['subItems'] || {}
    si = subitems[sub_item_id]
    raise 'Sub item not found' unless si
    msg = { 'id' => SecureRandom.uuid, 'authorId' => @user.username, 'authorName' => (@user.nickname.presence || @user.username), 'content' => content_text, 'timestamp' => Time.now.to_i }
    if si['type'] == 'channel'
      (si['messages'] ||= []) << msg
    else
      (si['posts'] ||= []) << msg
    end
    fc.update_json!(content)
  end

  def create_survey!(feature_id, title, questions_json)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    questions = JSON.parse(questions_json)
    content = fc.content_json
    content['surveys'] ||= {}
    content['responses'] ||= {}
    sid = "survey_#{(Time.now.to_f*1000).to_i}"
    content['surveys'][sid] = { 'id' => sid, 'title' => title, 'questions' => questions, 'created_by' => @user.username, 'created_at' => Time.now.to_f, 'status' => 'active' }
    content['responses'][sid] = {}
    fc.update_json!(content)
  end

  def submit_survey_response!(feature_id, survey_id, responses_json)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    responses = JSON.parse(responses_json)
    content = fc.content_json
    content['responses'] ||= {}
    content['responses'][survey_id] ||= {}
    content['responses'][survey_id][@user.username] = { 'responses' => responses, 'user' => @user.username, 'submitted_at' => Time.now.to_f }
    fc.update_json!(content)
  end

  def create_project!(feature_id, name, description)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    content['projects'] ||= {}
    pid = "project_#{(Time.now.to_f*1000).to_i}"
    content['projects'][pid] = { 'id' => pid, 'name' => name, 'description' => (description || ''), 'status' => 'active', 'created_by' => @user.username, 'created_at' => Time.now.to_f }
    fc.update_json!(content)
  end

  def create_task!(feature_id, project_id, title, description, priority)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    content['tasks'] ||= {}
    tid = "task_#{(Time.now.to_f*1000).to_i}"
    content['tasks'][tid] = { 'id' => tid, 'project_id' => project_id, 'title' => title, 'description' => (description || ''), 'priority' => (priority || 'medium'), 'status' => 'todo', 'created_by' => @user.username, 'created_at' => Time.now.to_f }
    fc.update_json!(content)
  end

  def update_task_status!(feature_id, task_id, status)
    fc = FeatureContent.find_by!(feature_id: feature_id)
    content = fc.content_json
    tasks = content['tasks'] || {}
    raise 'Task not found' unless tasks[task_id]
    tasks[task_id]['status'] = status
    tasks[task_id]['updated_at'] = Time.now.to_f
    fc.update_json!(content)
  end

  def update_feature_content!(feature_id, content_str)
    json = JSON.parse(content_str)
    fc = FeatureContent.find_by(feature_id: feature_id)
    if fc
      fc.update_json!(json)
    else
      FeatureContent.create!(feature_id: feature_id, content: json.to_json, updated_at: Time.current)
    end
  end
end
