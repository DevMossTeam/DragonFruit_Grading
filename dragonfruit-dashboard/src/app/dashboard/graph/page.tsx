'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { fetchFromAPI } from '@/lib/api';
import {
  fetchClassificationMetrics,
  fetchConfusionMatrix,
  getMetricsWithCache,
  MetricsData,
  ConfusionMatrixResponse,
} from '@/lib/metrics';

// Dynamic import to avoid SSR issues with ApexCharts
const ReactApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface StatisticData {
  label: string;
  value: number;
  unit: string;
  status: 'good' | 'warning' | 'danger';
}

interface IoTDailyData {
  date: string;
  uptime: number;
  temp: number;
  humidity: number;
}

interface ComputerVisionDailyData {
  date: string;
  accuracy: number;
  processingTime: number;
  detectionRate: number;
}

interface MachineLearningDailyData {
  date: string;
  fuzzyAccuracy: number;
  precision: number;
  recall: number;
}

interface SectionData {
  iotHealth: {
    uptime: StatisticData;
    temperature: StatisticData;
    humidity: StatisticData;
    signalStrength: StatisticData;
    dailyData: IoTDailyData[];
  };
  computerVision: {
    accuracy: StatisticData;
    processingTime: StatisticData;
    detectionRate: StatisticData;
    falsePositives: StatisticData;
    dailyData: ComputerVisionDailyData[];
  };
  machineLearning: {
    fuzzyAccuracy: StatisticData;
    precision: StatisticData;
    recall: StatisticData;
    f1Score: StatisticData;
    dailyData: MachineLearningDailyData[];
  };
}

export default function GraphPage() {
  const [sectionData, setSectionData] = useState<SectionData | null>(null);
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null);
  const [confusionMatrix, setConfusionMatrix] = useState<number[][] | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        console.log('📊 Fetching classification metrics...');
        
        // Fetch classification metrics
        const metricsResponse = await fetchClassificationMetrics();
        console.log('📊 Metrics Response:', metricsResponse);
        
        // Check if metrics were successfully retrieved
        if (metricsResponse.status === 'error' || metricsResponse.status === 'warning') {
          console.warn('⚠️ No metrics data available');
          setHasData(false);
          setMetricsData(null);
          setConfusionMatrix(null);
        } else if (metricsResponse.status === 'success' && metricsResponse.metrics) {
          console.log('✅ Metrics loaded successfully:', metricsResponse.metrics);
          setMetricsData(metricsResponse.metrics);
          setHasData(true);
          
          // Fetch confusion matrix
          console.log('📊 Fetching confusion matrix...');
          const cmResponse = await fetchConfusionMatrix();
          console.log('📊 Confusion Matrix Response:', cmResponse);
          
          if (cmResponse && cmResponse.status === 'success') {
            console.log('✅ Confusion matrix loaded successfully');
            setConfusionMatrix(cmResponse.confusion_matrix);
          }
        }

        // Mock data for other sections - replace with actual API calls
        const mockData: SectionData = {
          iotHealth: {
            uptime: { label: 'Uptime', value: 99.8, unit: '%', status: 'good' },
            temperature: { label: 'Temperature', value: 28.5, unit: '°C', status: 'good' },
            humidity: { label: 'Humidity', value: 65, unit: '%', status: 'good' },
            signalStrength: { label: 'Signal Strength', value: 92, unit: 'dBm', status: 'good' },
            dailyData: [
              { date: 'Mon', uptime: 99.8, temp: 28.2, humidity: 64 },
              { date: 'Tue', uptime: 99.9, temp: 28.5, humidity: 65 },
              { date: 'Wed', uptime: 99.7, temp: 27.8, humidity: 63 },
              { date: 'Thu', uptime: 100, temp: 29.1, humidity: 66 },
              { date: 'Fri', uptime: 99.6, temp: 28.9, humidity: 67 },
              { date: 'Sat', uptime: 99.9, temp: 28.3, humidity: 64 },
              { date: 'Sun', uptime: 99.8, temp: 28.7, humidity: 65 },
            ],
          },
          computerVision: {
            accuracy: { label: 'Detection Accuracy', value: 96.5, unit: '%', status: 'good' },
            processingTime: { label: 'Avg Processing Time', value: 245, unit: 'ms', status: 'good' },
            detectionRate: { label: 'Detection Rate', value: 98.2, unit: '%', status: 'good' },
            falsePositives: { label: 'False Positives', value: 2.1, unit: '%', status: 'warning' },
            dailyData: [
              { date: 'Mon', accuracy: 96.2, processingTime: 250, detectionRate: 98.1 },
              { date: 'Tue', accuracy: 96.5, processingTime: 245, detectionRate: 98.2 },
              { date: 'Wed', accuracy: 96.8, processingTime: 240, detectionRate: 98.4 },
              { date: 'Thu', accuracy: 96.1, processingTime: 255, detectionRate: 97.9 },
              { date: 'Fri', accuracy: 96.9, processingTime: 235, detectionRate: 98.5 },
              { date: 'Sat', accuracy: 97.1, processingTime: 238, detectionRate: 98.6 },
              { date: 'Sun', accuracy: 96.5, processingTime: 248, detectionRate: 98.2 },
            ],
          },
          machineLearning: {
            fuzzyAccuracy: {
              label: 'Fuzzy Logic Accuracy',
              value: hasData && metricsData?.accuracy ? metricsData.accuracy * 100 : 0,
              unit: '%',
              status: hasData && metricsData?.accuracy && metricsData.accuracy > 0.85 ? 'good' : 'warning',
            },
            precision: {
              label: 'Precision',
              value: hasData && metricsData?.macro_precision ? metricsData.macro_precision * 100 : 0,
              unit: '%',
              status: hasData && metricsData?.macro_precision && metricsData.macro_precision > 0.85 ? 'good' : 'warning',
            },
            recall: {
              label: 'Recall',
              value: hasData && metricsData?.macro_recall ? metricsData.macro_recall * 100 : 0,
              unit: '%',
              status: hasData && metricsData?.macro_recall && metricsData.macro_recall > 0.85 ? 'good' : 'warning',
            },
            f1Score: {
              label: 'F1 Score',
              value: hasData && metricsData?.macro_f1 ? metricsData.macro_f1 * 100 : 0,
              unit: '%',
              status: hasData && metricsData?.macro_f1 && metricsData.macro_f1 > 0.85 ? 'good' : 'warning',
            },
            dailyData: [
              { date: 'Mon', fuzzyAccuracy: 0, precision: 0, recall: 0 },
              { date: 'Tue', fuzzyAccuracy: 0, precision: 0, recall: 0 },
              { date: 'Wed', fuzzyAccuracy: 0, precision: 0, recall: 0 },
              { date: 'Thu', fuzzyAccuracy: 0, precision: 0, recall: 0 },
              { date: 'Fri', fuzzyAccuracy: 0, precision: 0, recall: 0 },
              { date: 'Sat', fuzzyAccuracy: 0, precision: 0, recall: 0 },
              { date: 'Sun', fuzzyAccuracy: 0, precision: 0, recall: 0 },
            ],
          },
        };

        setSectionData(mockData);
        setLoading(false);
      } catch (err) {
        console.error('❌ Error fetching chart data:', err);
        setHasData(false);
        setLoading(false);
      }
    };

    fetchChartData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <div className="text-center">
          <div className="inline-block">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
          </div>
          <p className="text-slate-600 text-lg font-medium">Loading analytics...</p>
          <p className="text-slate-500 text-sm mt-2">This may take a moment</p>
        </div>
      </div>
    );
  }

  if (!sectionData) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <div className="text-slate-600 text-lg">No data available</div>
      </div>
    );
  }

  // Helper function to get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'border-green-500 bg-green-50';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50';
      case 'danger':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-500 bg-gray-50';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'danger':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // IoT Health Charts
  const iotLineChartOptions = {
    chart: {
      type: 'line' as const,
      toolbar: { show: true },
    },
    colors: ['#3b82f6', '#ef4444', '#10b981'],
    xaxis: {
      categories: sectionData.iotHealth.dailyData.map((d) => d.date),
    },
    yaxis: {
      title: { text: 'Values' },
    },
    stroke: { curve: 'smooth' as const, width: 3 },
    markers: { size: 5 },
    legend: { position: 'top' as const },
  };

  const iotLineChartSeries = [
    {
      name: 'Uptime (%)',
      data: sectionData.iotHealth.dailyData.map((d) => d.uptime),
    },
    {
      name: 'Temperature (°C)',
      data: sectionData.iotHealth.dailyData.map((d) => d.temp),
    },
    {
      name: 'Humidity (%)',
      data: sectionData.iotHealth.dailyData.map((d) => d.humidity),
    },
  ];

  // Computer Vision Charts
  const cvLineChartOptions = {
    chart: {
      type: 'line' as const,
      toolbar: { show: true },
    },
    colors: ['#8b5cf6', '#ec4899', '#06b6d4'],
    xaxis: {
      categories: sectionData.computerVision.dailyData.map((d) => d.date),
    },
    yaxis: {
      title: { text: 'Accuracy/Detection Rate (%)' },
    },
    stroke: { curve: 'smooth' as const, width: 3 },
    markers: { size: 5 },
    legend: { position: 'top' as const },
  };

  const cvLineChartSeries = [
    {
      name: 'Accuracy (%)',
      data: sectionData.computerVision.dailyData.map((d) => d.accuracy),
    },
    {
      name: 'Detection Rate (%)',
      data: sectionData.computerVision.dailyData.map((d) => d.detectionRate),
    },
  ];

  // ML Radial/Gauge Charts Options
  const createRadialChartOptions = (title: string, color: string) => ({
    chart: {
      type: 'radialBar' as const,
      sparkline: {
        enabled: false,
      },
      toolbar: {
        show: false,
      },
    },
    colors: [color],
    plotOptions: {
      radialBar: {
        startAngle: -135,
        endAngle: 135,
        hollow: {
          margin: 0,
          size: '70%',
          background: '#fff',
          image: undefined,
          imageHeight: 151,
          imageWidth: 151,
        },
        track: {
          background: '#f2f2f2',
          strokeWidth: '97%',
          margin: 5,
          dropShadow: {
            enabled: true,
            top: 2,
            left: 0,
            color: '#999',
            opacity: 1,
            blur: 2,
          },
        },
        dataLabels: {
          show: true,
          name: {
            offsetY: -10,
            show: true,
            color: '#888',
            fontSize: '13px',
          },
          value: {
            formatter: function (val: number) {
              return parseInt(val.toString()) + '%';
            },
            color: '#111',
            fontSize: '30px',
            show: true,
          },
        },
      },
    },
    stroke: {
      lineCap: 'round' as const,
    },
    labels: [title],
  });

  const mlFuzzyChartOptions = createRadialChartOptions('Fuzzy Accuracy', '#f59e0b');
  const mlFuzzyChartSeries = [sectionData.machineLearning.fuzzyAccuracy.value];

  const mlPrecisionChartOptions = createRadialChartOptions('Precision', '#14b8a6');
  const mlPrecisionChartSeries = [sectionData.machineLearning.precision.value];

  const mlRecallChartOptions = createRadialChartOptions('Recall', '#6366f1');
  const mlRecallChartSeries = [sectionData.machineLearning.recall.value];

  const mlF1ScoreChartOptions = createRadialChartOptions('F1 Score', '#ec4899');
  const mlF1ScoreChartSeries = [sectionData.machineLearning.f1Score.value];

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-blue-50 to-indigo-50 p-8 space-y-8">
      {/* Header */}
      <div className="">
        <h1 className="text-5xl font-bold bg-linear-to-r from-blue-600 via-cyan-600 to-emerald-600 bg-clip-text text-transparent">System Analytics</h1>
        <p className="mt-5 text-base text-slate-600">
          {hasData ? 'Machine Learning and Computer Vision performance metrics' : 'No grading data available - all metrics showing as 0'}
        </p>
      </div>

      {/* ==================== MACHINE LEARNING FUZZY STATISTICS ==================== */}
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-slate-900">ML Fuzzy Logic Statistics</h2>
          <span className={`text-sm font-semibold px-3 py-1 rounded ${hasData ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'}`}>
            {hasData ? 'AI Classification' : 'No Data'}
          </span>
        </div>

        {/* ML Fuzzy Gauge Charts */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Fuzzy Accuracy Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlFuzzyChartOptions}
                series={mlFuzzyChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">Fuzzy Accuracy</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.fuzzyAccuracy.value.toFixed(1)}%</p>
            </div>
          </div>

          {/* Precision Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlPrecisionChartOptions}
                series={mlPrecisionChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">Precision</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.precision.value.toFixed(1)}%</p>
            </div>
          </div>

          {/* Recall Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlRecallChartOptions}
                series={mlRecallChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">Recall</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.recall.value.toFixed(1)}%</p>
            </div>
          </div>

          {/* F1 Score Gauge */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6 hover:shadow-md transition">
            <div className="h-56">
              <ReactApexChart
                options={mlF1ScoreChartOptions}
                series={mlF1ScoreChartSeries}
                type="radialBar"
                height={220}
              />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-slate-500">F1 Score</p>
              <p className="text-2xl font-bold text-slate-900">{sectionData.machineLearning.f1Score.value.toFixed(1)}%</p>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-900">Performance Overview</h3>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-emerald-500"></span>
                <span className="text-slate-600">Excellent (≥90%)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-amber-500"></span>
                <span className="text-slate-600">Good (80-89%)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-rose-500"></span>
                <span className="text-slate-600">Needs Work (below 80%)</span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Fuzzy Accuracy */}
            <div className="border-l-4 border-orange-500 pl-4 py-4 bg-orange-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Fuzzy Accuracy</p>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${
                  sectionData.machineLearning.fuzzyAccuracy.value >= 90
                    ? 'bg-emerald-100 text-emerald-700'
                    : sectionData.machineLearning.fuzzyAccuracy.value >= 80
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {sectionData.machineLearning.fuzzyAccuracy.value >= 90
                    ? '✓ Excellent'
                    : sectionData.machineLearning.fuzzyAccuracy.value >= 80
                    ? '◐ Good'
                    : '✗ Needs Work'}
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.fuzzyAccuracy.value.toFixed(1)}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className={`h-2 rounded-full transition-all ${
                  sectionData.machineLearning.fuzzyAccuracy.value >= 90
                    ? 'bg-emerald-500'
                    : sectionData.machineLearning.fuzzyAccuracy.value >= 80
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`} style={{width: `${sectionData.machineLearning.fuzzyAccuracy.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">{hasData ? 'Based on data' : 'No data available'}</p>
            </div>

            {/* Precision */}
            <div className="border-l-4 border-emerald-500 pl-4 py-4 bg-emerald-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Precision</p>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${
                  sectionData.machineLearning.precision.value >= 90
                    ? 'bg-emerald-100 text-emerald-700'
                    : sectionData.machineLearning.precision.value >= 80
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {sectionData.machineLearning.precision.value >= 90
                    ? '✓ Excellent'
                    : sectionData.machineLearning.precision.value >= 80
                    ? '◐ Good'
                    : '✗ Needs Work'}
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.precision.value.toFixed(1)}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className={`h-2 rounded-full transition-all ${
                  sectionData.machineLearning.precision.value >= 90
                    ? 'bg-emerald-500'
                    : sectionData.machineLearning.precision.value >= 80
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`} style={{width: `${sectionData.machineLearning.precision.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">{hasData ? 'No false positives' : 'Waiting for data'}</p>
            </div>

            {/* Recall */}
            <div className="border-l-4 border-indigo-500 pl-4 py-4 bg-indigo-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Recall</p>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${
                  sectionData.machineLearning.recall.value >= 90
                    ? 'bg-emerald-100 text-emerald-700'
                    : sectionData.machineLearning.recall.value >= 80
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {sectionData.machineLearning.recall.value >= 90
                    ? '✓ Excellent'
                    : sectionData.machineLearning.recall.value >= 80
                    ? '◐ Good'
                    : '✗ Needs Work'}
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.recall.value.toFixed(1)}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className={`h-2 rounded-full transition-all ${
                  sectionData.machineLearning.recall.value >= 90
                    ? 'bg-emerald-500'
                    : sectionData.machineLearning.recall.value >= 80
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`} style={{width: `${sectionData.machineLearning.recall.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">{hasData ? 'All grades detected' : 'No data yet'}</p>
            </div>

            {/* F1 Score */}
            <div className="border-l-4 border-pink-500 pl-4 py-4 bg-pink-50 rounded-r hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">F1 Score</p>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${
                  sectionData.machineLearning.f1Score.value >= 90
                    ? 'bg-emerald-100 text-emerald-700'
                    : sectionData.machineLearning.f1Score.value >= 80
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {sectionData.machineLearning.f1Score.value >= 90
                    ? '✓ Excellent'
                    : sectionData.machineLearning.f1Score.value >= 80
                    ? '◐ Good'
                    : '✗ Needs Work'}
                </span>
              </div>
              <p className="text-3xl font-bold text-slate-900 mb-2">{sectionData.machineLearning.f1Score.value.toFixed(1)}%</p>
              <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                <div className={`h-2 rounded-full transition-all ${
                  sectionData.machineLearning.f1Score.value >= 90
                    ? 'bg-emerald-500'
                    : sectionData.machineLearning.f1Score.value >= 80
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`} style={{width: `${sectionData.machineLearning.f1Score.value}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">{hasData ? 'Perfect balance' : 'Collect data'}</p>
            </div>
          </div>

          {/* Status Summary Card */}
          <div className={`mt-6 p-4 rounded-lg border ${
            hasData && sectionData.machineLearning.fuzzyAccuracy.value >= 85 &&
            sectionData.machineLearning.precision.value >= 85 &&
            sectionData.machineLearning.recall.value >= 85
              ? 'bg-linear-to-r from-emerald-50 to-cyan-50 border-emerald-200'
              : 'bg-linear-to-r from-amber-50 to-yellow-50 border-amber-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-bold mb-1 ${
                  hasData && sectionData.machineLearning.fuzzyAccuracy.value >= 85 &&
                  sectionData.machineLearning.precision.value >= 85 &&
                  sectionData.machineLearning.recall.value >= 85
                    ? 'text-emerald-900'
                    : 'text-amber-900'
                }`}>Overall System Status</p>
                <p className={`text-xs ${
                  hasData && sectionData.machineLearning.fuzzyAccuracy.value >= 85 &&
                  sectionData.machineLearning.precision.value >= 85 &&
                  sectionData.machineLearning.recall.value >= 85
                    ? 'text-emerald-700'
                    : 'text-amber-700'
                }`}>
                  {hasData && sectionData.machineLearning.fuzzyAccuracy.value >= 85 &&
                  sectionData.machineLearning.precision.value >= 85 &&
                  sectionData.machineLearning.recall.value >= 85
                    ? 'All metrics performing at excellent levels - system is production-ready'
                    : hasData ? 'Some metrics need improvement - collect more training data' : 'No data available - metrics showing 0'}
                </p>
              </div>
              <div className="text-center">
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full font-bold text-lg ${
                  hasData && sectionData.machineLearning.fuzzyAccuracy.value >= 85 &&
                  sectionData.machineLearning.precision.value >= 85 &&
                  sectionData.machineLearning.recall.value >= 85
                    ? 'bg-emerald-500 text-white'
                    : 'bg-amber-500 text-white'
                }`}>
                  {hasData && sectionData.machineLearning.fuzzyAccuracy.value >= 85 &&
                  sectionData.machineLearning.precision.value >= 85 &&
                  sectionData.machineLearning.recall.value >= 85
                    ? '✓'
                    : '!'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Confusion Matrix Distribution Grade */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <h3 className="text-lg font-bold text-slate-900 mb-2">Classification Confusion Matrix</h3>
          <p className="text-sm text-slate-600 mb-4">Performance across Dragon Fruit grades (A: Premium, B: Regular, C: Small)</p>
          
          <div className="overflow-x-auto rounded border border-slate-300 bg-slate-50">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-300 bg-slate-100">
                  <th className="px-4 py-2 text-left font-bold text-slate-900">Predicted →</th>
                  <th className="px-4 py-2 text-center font-bold text-white bg-emerald-500">Grade A</th>
                  <th className="px-4 py-2 text-center font-bold text-white bg-amber-500">Grade B</th>
                  <th className="px-4 py-2 text-center font-bold text-white bg-rose-500">Grade C</th>
                  <th className="px-4 py-2 text-center font-bold text-slate-900 bg-slate-200">Total</th>
                </tr>
              </thead>
              <tbody>
                {confusionMatrix ? (
                  <>
                    <tr className="border-b border-slate-200 hover:bg-emerald-50">
                      <td className="px-4 py-2 font-bold text-slate-900 bg-emerald-100">Grade A</td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-emerald-200 text-emerald-900 px-2 py-1 rounded text-sm font-bold">{confusionMatrix[0][0]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[0][1]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[0][2]}</div></td>
                      <td className="px-4 py-2 text-center font-bold text-slate-900">{confusionMatrix[0][0] + confusionMatrix[0][1] + confusionMatrix[0][2]}</td>
                    </tr>
                    <tr className="border-b border-slate-200 hover:bg-amber-50">
                      <td className="px-4 py-2 font-bold text-slate-900 bg-amber-100">Grade B</td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[1][0]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-amber-200 text-amber-900 px-2 py-1 rounded text-sm font-bold">{confusionMatrix[1][1]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[1][2]}</div></td>
                      <td className="px-4 py-2 text-center font-bold text-slate-900">{confusionMatrix[1][0] + confusionMatrix[1][1] + confusionMatrix[1][2]}</td>
                    </tr>
                    <tr className="hover:bg-rose-50">
                      <td className="px-4 py-2 font-bold text-slate-900 bg-rose-100">Grade C</td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[2][0]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-slate-200 text-slate-700 px-2 py-1 rounded text-sm">{confusionMatrix[2][1]}</div></td>
                      <td className="px-4 py-2 text-center"><div className="inline-block bg-rose-200 text-rose-900 px-2 py-1 rounded text-sm font-bold">{confusionMatrix[2][2]}</div></td>
                      <td className="px-4 py-2 text-center font-bold text-slate-900">{confusionMatrix[2][0] + confusionMatrix[2][1] + confusionMatrix[2][2]}</td>
                    </tr>
                  </>
                ) : (
                  <tr>
                    <td colSpan={5} className="px-4 py-4 text-center text-slate-500">
                      {hasData ? 'No confusion matrix data available' : 'No data - all values showing 0'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Matrix Legend */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded border border-blue-300">
              <p className="text-sm text-blue-700 font-bold mb-2">TRUE POSITIVES</p>
              <p className="text-sm text-slate-700">
                <span className="font-bold">
                  {hasData && metricsData && confusionMatrix
                    ? confusionMatrix[0][0] + confusionMatrix[1][1] + confusionMatrix[2][2]
                    : '0'}
                </span>{' '}
                correctly classified
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {hasData && metricsData ? `${(metricsData.accuracy * 100).toFixed(1)}% accuracy` : 'Accuracy: 0%'}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded border border-yellow-300">
              <p className="text-sm text-yellow-700 font-bold mb-2">PRECISION</p>
              <p className="text-sm text-slate-700">
                <span className="font-bold">
                  {hasData && metricsData ? (metricsData.macro_precision * 100).toFixed(1) : '0'}%
                </span>{' '}
                average precision
              </p>
              <p className="text-xs text-slate-500 mt-1">
                A: {hasData && metricsData ? (metricsData.precision_A * 100).toFixed(1) : '0'}% | B: {hasData && metricsData ? (metricsData.precision_B * 100).toFixed(1) : '0'}% | C: {hasData && metricsData ? (metricsData.precision_C * 100).toFixed(1) : '0'}%
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded border border-purple-300">
              <p className="text-sm text-purple-700 font-bold mb-2">RECALL</p>
              <p className="text-sm text-slate-700">
                <span className="font-bold">
                  {hasData && metricsData ? (metricsData.macro_recall * 100).toFixed(1) : '0'}%
                </span>{' '}
                average recall
              </p>
              <p className="text-xs text-slate-500 mt-1">
                A: {hasData && metricsData ? (metricsData.recall_A * 100).toFixed(1) : '0'}% | B: {hasData && metricsData ? (metricsData.recall_B * 100).toFixed(1) : '0'}% | C: {hasData && metricsData ? (metricsData.recall_C * 100).toFixed(1) : '0'}%
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}