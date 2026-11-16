// HourlySpawnTable — 24-hour spawn rate table derived from real exam volume data.
// Each hour maps to: exams_per_hour, spawn_weight, acuity_bias.
// acuity_bias: 0.0–1.0 — higher = more high-acuity patients that hour.

using System.Collections.Generic;

namespace CTDash
{
    public struct SpawnHourEntry
    {
        public int   ExamsPerHour;
        public float SpawnWeight;
        public float AcuityBias;
    }

    public static class HourlySpawnTable
    {
        public static readonly Dictionary<int, SpawnHourEntry> Table = new Dictionary<int, SpawnHourEntry>
        {
            {  0, new SpawnHourEntry { ExamsPerHour =  4, SpawnWeight = 0.25f, AcuityBias = 0.60f } },
            {  1, new SpawnHourEntry { ExamsPerHour =  3, SpawnWeight = 0.20f, AcuityBias = 0.60f } },
            {  2, new SpawnHourEntry { ExamsPerHour =  3, SpawnWeight = 0.20f, AcuityBias = 0.60f } },
            {  3, new SpawnHourEntry { ExamsPerHour =  3, SpawnWeight = 0.20f, AcuityBias = 0.60f } },
            {  4, new SpawnHourEntry { ExamsPerHour =  4, SpawnWeight = 0.25f, AcuityBias = 0.50f } },
            {  5, new SpawnHourEntry { ExamsPerHour =  4, SpawnWeight = 0.25f, AcuityBias = 0.50f } },
            {  6, new SpawnHourEntry { ExamsPerHour =  5, SpawnWeight = 0.30f, AcuityBias = 0.40f } },
            {  7, new SpawnHourEntry { ExamsPerHour =  7, SpawnWeight = 0.45f, AcuityBias = 0.40f } },
            {  8, new SpawnHourEntry { ExamsPerHour = 10, SpawnWeight = 0.65f, AcuityBias = 0.35f } },
            {  9, new SpawnHourEntry { ExamsPerHour = 13, SpawnWeight = 0.80f, AcuityBias = 0.35f } },
            { 10, new SpawnHourEntry { ExamsPerHour = 15, SpawnWeight = 0.90f, AcuityBias = 0.30f } },
            { 11, new SpawnHourEntry { ExamsPerHour = 17, SpawnWeight = 1.00f, AcuityBias = 0.30f } },
            { 12, new SpawnHourEntry { ExamsPerHour = 18, SpawnWeight = 1.00f, AcuityBias = 0.30f } },
            { 13, new SpawnHourEntry { ExamsPerHour = 17, SpawnWeight = 1.00f, AcuityBias = 0.30f } },
            { 14, new SpawnHourEntry { ExamsPerHour = 16, SpawnWeight = 0.95f, AcuityBias = 0.30f } },
            { 15, new SpawnHourEntry { ExamsPerHour = 16, SpawnWeight = 0.95f, AcuityBias = 0.30f } },
            { 16, new SpawnHourEntry { ExamsPerHour = 16, SpawnWeight = 0.95f, AcuityBias = 0.30f } },
            { 17, new SpawnHourEntry { ExamsPerHour = 15, SpawnWeight = 0.90f, AcuityBias = 0.35f } },
            { 18, new SpawnHourEntry { ExamsPerHour = 12, SpawnWeight = 0.75f, AcuityBias = 0.40f } },
            { 19, new SpawnHourEntry { ExamsPerHour =  9, SpawnWeight = 0.55f, AcuityBias = 0.45f } },
            { 20, new SpawnHourEntry { ExamsPerHour =  7, SpawnWeight = 0.45f, AcuityBias = 0.50f } },
            { 21, new SpawnHourEntry { ExamsPerHour =  6, SpawnWeight = 0.38f, AcuityBias = 0.55f } },
            { 22, new SpawnHourEntry { ExamsPerHour =  5, SpawnWeight = 0.30f, AcuityBias = 0.60f } },
            { 23, new SpawnHourEntry { ExamsPerHour =  4, SpawnWeight = 0.25f, AcuityBias = 0.60f } },
        };
    }
}
