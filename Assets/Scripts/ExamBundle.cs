// Scripts/ExamBundle.cs
public class ExamBundle
{
    public string Name;
    public float ScanTime;
    public int Weight;

    public ExamBundle(string name, float scanTime, int weight = 1)
    {
        Name = name;
        ScanTime = scanTime;
        Weight = weight;
    }
}
