"""
Performance Benchmarking Utility
Production Tool: Measure API performance and identify bottlenecks

Run with: python performance_benchmark.py
"""

import asyncio
import time
from typing import Dict, List
import statistics


class PerformanceBenchmark:
    """Simple performance benchmarking utility"""

    def __init__(self):
        self.results = {}

    def measure(self, name: str, func, *args, **kwargs):
        """Measure execution time of a function"""
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        if name not in self.results:
            self.results[name] = []
        self.results[name].append(duration)

        return result, duration

    async def measure_async(self, name: str, func, *args, **kwargs):
        """Measure execution time of an async function"""
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start

        if name not in self.results:
            self.results[name] = []
        self.results[name].append(duration)

        return result, duration

    def get_stats(self, name: str) -> Dict:
        """Get statistics for a benchmark"""
        if name not in self.results or not self.results[name]:
            return {}

        durations = self.results[name]
        return {
            "count": len(durations),
            "min": min(durations),
            "max": max(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "stddev": statistics.stdev(durations) if len(durations) > 1 else 0
        }

    def print_report(self):
        """Print formatted benchmark report"""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("=" * 80)

        for name in sorted(self.results.keys()):
            stats = self.get_stats(name)
            if stats:
                print(f"\n{name}:")
                print(f"  Count:  {stats['count']}")
                print(f"  Min:    {stats['min']*1000:.2f}ms")
                print(f"  Max:    {stats['max']*1000:.2f}ms")
                print(f"  Mean:   {stats['mean']*1000:.2f}ms")
                print(f"  Median: {stats['median']*1000:.2f}ms")
                print(f"  StdDev: {stats['stddev']*1000:.2f}ms")

        print("\n" + "=" * 80)


# Example usage
async def example_benchmarks():
    """Example benchmarks for key operations"""
    benchmark = PerformanceBenchmark()

    print("Running performance benchmarks...")

    # Simulate database query
    async def mock_db_query():
        await asyncio.sleep(0.05)  # 50ms
        return {"data": "result"}

    # Simulate LLM API call
    async def mock_llm_call():
        await asyncio.sleep(2.0)  # 2 seconds
        return {"analysis": "complete"}

    # Simulate data processing
    def mock_processing():
        time.sleep(0.01)  # 10ms
        return [1, 2, 3, 4, 5]

    # Run benchmarks
    for i in range(10):
        await benchmark.measure_async("database_query", mock_db_query)
        benchmark.measure("data_processing", mock_processing)

    for i in range(3):
        await benchmark.measure_async("llm_api_call", mock_llm_call)

    # Print report
    benchmark.print_report()


# Specific benchmarks for LCT features
async def benchmark_analysis_features():
    """Benchmark the three AI analysis features"""
    from unittest.mock import AsyncMock, MagicMock, patch
    import sys

    # Mock anthropic
    sys.modules['anthropic'] = MagicMock()

    from services.simulacra_detector import SimulacraDetector
    from services.bias_detector import BiasDetector
    from services.frame_detector import FrameDetector

    benchmark = PerformanceBenchmark()
    mock_session = AsyncMock()

    # Mock database results
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    print("\nBenchmarking AI Analysis Features...")

    with patch('services.simulacra_detector.anthropic'), \
         patch('services.bias_detector.anthropic'), \
         patch('services.frame_detector.anthropic'):

        # Benchmark Simulacra
        simulacra = SimulacraDetector(mock_session)
        for i in range(5):
            await benchmark.measure_async(
                "simulacra_get_results",
                simulacra.get_conversation_results,
                "test-uuid"
            )

        # Benchmark Bias
        bias = BiasDetector(mock_session)
        for i in range(5):
            await benchmark.measure_async(
                "bias_get_results",
                bias.get_conversation_results,
                "test-uuid"
            )

        # Benchmark Frame
        frame = FrameDetector(mock_session)
        for i in range(5):
            await benchmark.measure_async(
                "frame_get_results",
                frame.get_conversation_results,
                "test-uuid"
            )

    benchmark.print_report()


if __name__ == "__main__":
    print("Live Conversational Threads - Performance Benchmarks")
    print("=" * 80)

    # Run example benchmarks
    asyncio.run(example_benchmarks())

    # Run feature-specific benchmarks
    try:
        asyncio.run(benchmark_analysis_features())
    except Exception as e:
        print(f"\nWarning: Could not run analysis benchmarks: {e}")
        print("This is normal if running outside the project directory.")

    print("\nBenchmarking complete!")
