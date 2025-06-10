// User Types
export interface User {
    id: number;
    email: string;
    fullName: string;
    role: 'admin' | 'analyst' | 'compliance';
    isActive: boolean;
    createdAt: string;
    lastLogin?: string;
}

// Transaction Types
export interface Transaction {
    id: number;
    transactionId: string;
    amount: number;
    currency: string;
    timestamp: string;
    status: 'pending' | 'completed' | 'failed';
    metadata: Record<string, any>;
    isAnomaly: boolean;
    anomalyScore?: number;
    anomalyDetails?: Record<string, any>;
}

// Compliance Types
export interface ComplianceLog {
    id: number;
    eventType: 'transaction' | 'system' | 'userAction';
    eventId: string;
    timestamp: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    metadata: Record<string, any>;
    isResolved: boolean;
    resolutionNotes?: string;
}

// System Metric Types
export interface SystemMetric {
    id: number;
    metricName: string;
    value: number;
    timestamp: string;
    labels: Record<string, string>;
    isAnomaly: boolean;
    anomalyScore?: number;
}

// Incident Types
export interface Incident {
    id: number;
    incidentId: string;
    title: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    status: 'open' | 'investigating' | 'resolved' | 'closed';
    createdAt: string;
    updatedAt: string;
    resolvedAt?: string;
    assignedTo?: number;
    metadata: Record<string, any>;
}

// Anomaly Detection Types
export interface AnomalyDetectionRequest {
    data: Record<string, any>[];
    modelType: 'isolation_forest' | 'knn';
    parameters?: Record<string, any>;
}

export interface AnomalyDetectionResponse {
    anomalies: {
        index: number;
        isAnomaly: boolean;
        score: number;
        data: Record<string, any>;
    }[];
    scores: number[];
    modelMetadata: Record<string, any>;
}

// API Response Types
export interface ApiResponse<T> {
    data: T;
    message?: string;
    error?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
}

// Compliance Stats Types
export interface ComplianceStats {
    totalLogs: number;
    resolvedLogs: number;
    unresolvedLogs: number;
    severityDistribution: Record<string, number>;
} 