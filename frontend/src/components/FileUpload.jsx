import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'

const FileUpload = ({ onUploadSuccess, isLoading, setIsLoading }) => {
  const [uploadStatus, setUploadStatus] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsLoading(true)
    setUploadStatus('uploading')
    setUploadedFile(file)

    try {
      const response = await api.uploadResume(file)
      setUploadStatus('success')
      toast.success(`File "${file.name}" uploaded successfully!`)
      onUploadSuccess(response.session_id, file.name)
    } catch (error) {
      setUploadStatus('error')
      toast.error(error.message || 'Upload failed')
      console.error('Upload error:', error)
    } finally {
      setIsLoading(false)
    }
  }, [onUploadSuccess, setIsLoading])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md']
    },
    multiple: false,
    disabled: isLoading
  })

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : uploadStatus === 'success'
            ? 'border-green-500 bg-green-50'
            : uploadStatus === 'error'
            ? 'border-red-500 bg-red-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
          ${isLoading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {uploadStatus === 'uploading' ? (
            <div className="animate-pulse">
              <Upload className="h-12 w-12 text-primary-500" />
            </div>
          ) : uploadStatus === 'success' ? (
            <CheckCircle className="h-12 w-12 text-green-500" />
          ) : uploadStatus === 'error' ? (
            <AlertCircle className="h-12 w-12 text-red-500" />
          ) : (
            <FileText className="h-12 w-12 text-gray-400" />
          )}
          
          <div>
            {uploadStatus === 'uploading' ? (
              <p className="text-primary-600 font-medium">Uploading file...</p>
            ) : uploadStatus === 'success' ? (
              <div>
                <p className="text-green-600 font-medium">File uploaded successfully!</p>
                {uploadedFile && (
                  <p className="text-sm text-gray-600 mt-1">{uploadedFile.name}</p>
                )}
              </div>
            ) : uploadStatus === 'error' ? (
              <p className="text-red-600 font-medium">Upload failed. Please try again.</p>
            ) : isDragActive ? (
              <p className="text-primary-600 font-medium">Drop the file here...</p>
            ) : (
              <div>
                <p className="text-gray-700 font-medium">
                  Drag & drop your resume here, or click to select
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Supports PDF, TXT, DOCX, and MD files
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {uploadedFile && uploadStatus === 'success' && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-green-800 font-medium">Ready for Analysis</p>
              <p className="text-green-600 text-sm">
                {uploadedFile.name} • {(uploadedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload
