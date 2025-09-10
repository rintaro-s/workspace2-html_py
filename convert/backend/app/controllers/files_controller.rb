class FilesController < ApplicationController
  def serve
    path = params[:path]
    abs = Rails.root.join('files', path)
    alt = Rails.root.join('..', '..', 'files', path)
    file_path = if File.exist?(abs) && File.file?(abs)
      abs
    elsif File.exist?(alt) && File.file?(alt)
      alt
    end
    if file_path
      send_file file_path, disposition: 'inline'
    else
      render json: { error: 'File not found' }, status: 404
    end
  end

  # 互換: /file/:filename -> /files/uploads/:filename
  def serve_single
    filename = params[:filename]
    abs = Rails.root.join('files', 'uploads', filename)
    alt = Rails.root.join('..', '..', 'files', 'uploads', filename)
    file_path = if File.exist?(abs) && File.file?(abs)
      abs
    elsif File.exist?(alt) && File.file?(alt)
      alt
    end
    if file_path
      send_file file_path, disposition: 'inline'
    else
      render json: { error: 'File not found' }, status: 404
    end
  end
end
